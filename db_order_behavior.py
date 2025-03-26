import psycopg2
from datetime import datetime, timedelta
from db_order_anomaly_log import log_delivery_anomalies

# --- Database Connection Helper ---
def get_db_connection():
    return psycopg2.connect(
        dbname="your_db_name",
        user="your_username",
        password="your_password",
        host="localhost",
        port="5432"
    )

# --- Inventory Check ---
def get_inventory_status(conn, product_id):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT current_pellets, to_be_received, capacity_pellets
            FROM inventory
            WHERE inventory_id = 1;
        """)
        return cur.fetchone()

# --- Get Pallet Cost ---
def get_pallet_cost(conn, product_id):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT pallet_cost FROM product_pellets
            WHERE product_id = %s;
        """, (product_id,))
        result = cur.fetchone()
        return result[0] if result else 0.0

# --- Request Resupply ---
def request_resupply(conn, product_id, quantity):
    current, incoming, capacity = get_inventory_status(conn, product_id)
    available_space = capacity - (current + incoming)
    batches = []
    while quantity > 0:
        batch = min(quantity, available_space)
        if batch <= 0:
            break
        batches.append(batch)
        quantity -= batch
    now = datetime.now()
    for qty in batches:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO supplier_delivery (
                    supplier_id, expected_delivery_time, order_sent, status,
                    cost, product_id, quantity_received, date_time
                ) VALUES (
                    (SELECT supplier_id FROM supplier WHERE product_id = %s LIMIT 1),
                    INTERVAL '2 days', %s, 'pending', 0, %s, %s, %s
                );
            """, (product_id, now, product_id, qty, now))
    conn.commit()

# --- Get Available Driver ---
def get_available_driver(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT employee_id FROM employee
            WHERE job_role = 'driver'
            AND employee_id NOT IN (
                SELECT driver_sent FROM inventory_delivery
                WHERE time_returned IS NULL
            ) LIMIT 1;
        """)
        res = cur.fetchone()
        return res[0] if res else None

# --- Get Available Truck ---
def get_available_truck(conn, required_weight, refrigeration_needed):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT truck_id, capacity, refrigerated
            FROM truck
            WHERE operational_status = 'available'
            AND (refrigerated = TRUE OR %s = FALSE)
        """, (refrigeration_needed,))
        trucks = cur.fetchall()
        for truck_id, capacity, _ in trucks:
            if capacity >= required_weight:
                return truck_id
    return None

# --- Add to Queue Logging ---
def log_loading_queue(conn, truck_id, employee_id, quantity):
    now = datetime.now()
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO loading_queue (
                forklift_id, employee_id, expected_time,
                start_time, finalized_time, quantity, truck_id, date_time
            ) VALUES (
                1, %s, INTERVAL '30 minutes', %s, %s, %s, %s, %s
            );
        """, (employee_id, now, now + timedelta(minutes=30), quantity, truck_id, now))
    conn.commit()

# --- Log Transaction ---
def log_transaction(conn, delivery_id, cost):
    now = datetime.now()
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO transactions (
                transaction_id, type, cost, date, date_time
            ) VALUES (%s, 'delivery', %s, %s, %s);
        """, (delivery_id, cost, now.date(), now))
    conn.commit()

# --- Schedule Delivery ---
def schedule_delivery(conn, store_id, products, truck_id, driver_id):
    now = datetime.now()
    closing_time = datetime.combine(now.date(), datetime.strptime("20:00", "%H:%M").time())
    estimated_return_time = now + timedelta(hours=3)
    time_sent = now if estimated_return_time <= (closing_time - timedelta(hours=1)) else datetime.combine(now.date() + timedelta(days=1), datetime.strptime("04:00", "%H:%M").time())

    for item in products:
        pallet_cost = get_pallet_cost(conn, item['product_id'])
        cost = pallet_cost * item['quantity']

        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO inventory_delivery (
                    store_sent, products_delivered, quantities_delivered, cost,
                    truck_sent, driver_sent, time_sent, status, date_time
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'scheduled', %s)
                RETURNING transaction_id;
            """, (
                store_id, str(item['product_id']), item['quantity'], cost,
                truck_id, driver_id, time_sent, now
            ))
            delivery_id = cur.fetchone()[0]

            cur.execute("""
                UPDATE inventory
                SET current_pellets = current_pellets - %s,
                    to_be_sent = to_be_sent + %s
                WHERE inventory_id = 1;
            """, (item['quantity'], item['quantity']))

        log_transaction(conn, delivery_id, cost)
        # Log anomalies after scheduling
        expected_cost = pallet_cost * item['quantity']
        log_delivery_anomalies(
            conn,
            transaction_id=delivery_id,
            expected_cost=expected_cost,
            actual_cost=cost,
            driver_id=driver_id,
            delivery_start=now,
            delivery_end=estimated_return_time
        )

    log_loading_queue(conn, truck_id, driver_id, sum([x['quantity'] for x in products]))
    conn.commit()

# --- Fulfillment Engine ---
def fulfill_orders():
    conn = get_db_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT store_id, products, date_time
                FROM pending_orders
                ORDER BY date_time ASC;
            """)
            orders = cur.fetchall()
            for store_id, products_json, order_time in orders:
                total_weight = 0
                refrigeration_required = False
                prepared_items = []

                for item in products_json:  # assuming item is a dict with keys: product_id, quantity, weight, refrigerated
                    available, _, _ = get_inventory_status(conn, item['product_id'])
                    deliver_now = min(item['quantity'], available)
                    if deliver_now > 0:
                        prepared_items.append({
                            'product_id': item['product_id'],
                            'quantity': deliver_now,
                            'weight': item['weight'] * deliver_now
                        })
                        total_weight += item['weight'] * deliver_now
                    if deliver_now < item['quantity']:
                        request_resupply(conn, item['product_id'], item['quantity'] - deliver_now)
                    if item['refrigerated']:
                        refrigeration_required = True

                if not prepared_items:
                    continue

                driver_id = get_available_driver(conn)
                if not driver_id:
                    continue

                truck_id = get_available_truck(conn, total_weight, refrigeration_required)
                if not truck_id:
                    continue

                schedule_delivery(conn, store_id, prepared_items, truck_id, driver_id)

if __name__ == "__main__":
    fulfill_orders()
