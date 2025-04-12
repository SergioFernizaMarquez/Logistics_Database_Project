from datetime import datetime, timedelta
import json, random
from db_order_anomaly_log import log_delivery_anomalies  # Make sure this function now accepts a delivery_id argument.
from db_config import get_db_connection

# --- Inventory Check ---
def get_inventory_status(conn, product_id):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT current_pellets, to_be_sent, to_be_received, capacity_pellets
            FROM inventory
            WHERE inventory_id = 1;
        """, (product_id,))
        return cur.fetchone()

# --- Get Pallet Cost ---
def get_pallet_cost(conn, product_id):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT pallet_cost FROM product_pellets
            WHERE product_id = %s;
        """, (product_id,))
        result = cur.fetchone()
        return float(result[0]) if result is not None and result[0] is not None else 0.0

# --- Get Expected Delivery Time for Store ---
def get_store_expected_time(conn, store_id):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT expected_time FROM store
            WHERE store_id = %s;
        """, (store_id,))
        result = cur.fetchone()
        return result[0] if result is not None and result[0] is not None else timedelta(hours=2)

# --- Get Store Distance ---
def get_store_distance(conn, store_id):
    with conn.cursor() as cur:
        cur.execute("SELECT distance_km FROM store WHERE store_id = %s;", (store_id,))
        result = cur.fetchone()
        return float(result[0]) if result is not None and result[0] is not None else 0.0

# --- Request Resupply ---
def request_resupply(conn, product_id, quantity, current_date):
    current, _, to_be_received, capacity = get_inventory_status(conn, product_id)
    available_space = capacity - (current + to_be_received)
    batches = []
    while quantity > 0:
        batch = min(quantity, available_space)
        if batch <= 0:
            break
        batches.append(batch)
        quantity -= batch
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
            """, (product_id, current_date, product_id, qty, current_date))
    conn.commit()

# --- Helper: Get Driver for Truck ---
def get_driver_for_truck(conn, truck_id):
    """
    Returns the driver (employee_id) associated with the given truck.
    """
    with conn.cursor() as cur:
        cur.execute("SELECT employee_id FROM truck WHERE truck_id = %s;", (truck_id,))
        result = cur.fetchone()
        return result[0] if result is not None else None

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

# --- Update Truck Status ---
def update_truck_status(conn, truck_id, status):
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE truck
            SET operational_status = %s
            WHERE truck_id = %s;
        """, (status, truck_id))
    conn.commit()

# --- Check and Enforce Truck Maintenance ---
def enforce_truck_maintenance(conn, truck_id, current_date):
    with conn.cursor() as cur:
        cur.execute("SELECT last_maintanance FROM truck WHERE truck_id = %s;", (truck_id,))
        result = cur.fetchone()
        if result is None:
            return False
        last_maintanance = result[0]
        if last_maintanance is not None and (current_date - last_maintanance).days >= 200:
            update_truck_status(conn, truck_id, 'maintenance')
            cur.execute("UPDATE truck SET last_maintanance = %s WHERE truck_id = %s;", (current_date, truck_id))
            conn.commit()
            return True
    return False

# --- Mark Product Pellets as Sent (FEFO) ---
def mark_product_pellets_as_sent(conn, product_id, quantity, current_date):
    with conn.cursor() as cur:
        cur.execute("SELECT name FROM product_pellets WHERE product_id = %s;", (product_id,))
        result = cur.fetchone()
        if not result:
            return []
        product_name = result[0]
    with conn.cursor() as cur:
        cur.execute("""
            SELECT pellet_id FROM product_pellet
            WHERE name = %s AND sent = FALSE
            ORDER BY sell_by ASC
            LIMIT %s;
        """, (product_name, quantity))
        pellets = cur.fetchall()
        pellet_ids = [p[0] for p in pellets]
    if pellet_ids:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE product_pellet
                SET sent = TRUE
                WHERE pellet_id = ANY(%s);
            """, (pellet_ids,))
    conn.commit()
    return pellet_ids

# --- Log Transaction ---
def log_transaction(conn, cost, transaction_type, current_date):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO transactions (type, cost, date, date_time)
            VALUES (%s, %s, %s, %s)
            RETURNING transaction_id;
        """, (transaction_type, cost, current_date, current_date))
        return cur.fetchone()[0]

# --- Get Current Gas Price ---
def get_current_gas_price(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT value FROM system_config WHERE key = 'current_gas_price';")
        result = cur.fetchone()
        return float(result[0]) if result is not None and result[0] is not None else 3.0

# --- Refuel Truck After Delivery ---
def refuel_truck_after_delivery(conn, truck_id, driver_id, km_driven, current_date):
    gas_price = get_current_gas_price(conn)
    liters_used = km_driven / 3.0
    cost = round(liters_used * gas_price, 2)
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO transactions (type, cost, date, date_time)
            VALUES ('fuel', %s, %s, %s)
            RETURNING transaction_id;
        """, (cost, current_date, current_date))
        transaction_id = cur.fetchone()[0]
        cur.execute("""
            INSERT INTO fuel_log (transaction_id, truck_id, employee_id, cost, liters, cost_per_liter, expected_cost, date_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """, (transaction_id, truck_id, driver_id, cost, liters_used, gas_price, cost, current_date))
    conn.commit()

# --- Fulfill Orders ---
def fulfill_orders(current_date):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT store_id, products, date_time
                FROM pending_orders
                ORDER BY date_time ASC;
            """)
            orders = cur.fetchall()
        for store_id, products_json, order_time in orders:
            try:
                total_weight = 0
                refrigeration_required = False
                prepared_items = []  # List of items to be delivered.
                products = json.loads(products_json) if isinstance(products_json, str) else products_json
                for item in products:
                    available, _, _, _ = get_inventory_status(conn, item['product_id'])
                    deliver_now = min(item['quantity'], available)
                    if deliver_now > 0:
                        prepared_items.append({
                            'product_id': item['product_id'],
                            'quantity': deliver_now,
                            'weight': item['weight'] * deliver_now,
                            'refrigerated': item.get('refrigerated', False)
                        })
                        total_weight += item['weight'] * deliver_now
                    if deliver_now < item['quantity']:
                        request_resupply(conn, item['product_id'], item['quantity'] - deliver_now, current_date)
                    if item.get('refrigerated', False):
                        refrigeration_required = True
                if not prepared_items:
                    continue
                # Get truck and then use its driver.
                truck_id = get_available_truck(conn, total_weight, refrigeration_required)
                if not truck_id:
                    print(f"No available truck for order from store {store_id} with total weight {total_weight}.")
                    continue
                driver_id = get_driver_for_truck(conn, truck_id)
                if not driver_id:
                    print(f"Truck {truck_id} does not have an associated driver.")
                    continue
                if enforce_truck_maintenance(conn, truck_id, current_date):
                    print(f"Truck {truck_id} is under maintenance on {current_date}.")
                    continue
                schedule_delivery(conn, store_id, prepared_items, truck_id, driver_id, current_date)
                # Update inventory: subtract delivered quantities and add to to_be_sent.
                with conn.cursor() as cur:
                    for item in products:
                        cur.execute("""
                            UPDATE inventory
                            SET current_pellets = GREATEST(current_pellets - %s, 0),
                                to_be_sent = to_be_sent + %s
                            WHERE inventory_id = 1;
                        """, (item['quantity'], item['quantity']))
                    cur.execute("""
                        DELETE FROM pending_orders
                        WHERE store_id = %s AND date_time = %s;
                    """, (store_id, order_time))
                conn.commit()
            except Exception as order_error:
                print(f"Error processing order for store {store_id} at {order_time}: {order_error}")
                continue
    except Exception as e:
        print(f"Error in fulfill_orders: {e}")

# --- Schedule Delivery ---
def schedule_delivery(conn, store_id, products, truck_id, driver_id, current_date):
    store_expected_time = get_store_expected_time(conn, store_id)
    simulation_start = datetime.strptime("08:00", "%H:%M").time()
    now_dt = datetime.combine(current_date, simulation_start)
    loading_end = now_dt + timedelta(hours=1)
    estimated_return_time = now_dt + (store_expected_time * 2) + timedelta(hours=1)
    closing_time_dt = datetime.combine(current_date, datetime.strptime("20:00", "%H:%M").time())
    if estimated_return_time > (closing_time_dt - timedelta(hours=1)):
        time_sent = datetime.combine(current_date + timedelta(days=1), datetime.strptime("04:00", "%H:%M").time())
    else:
        time_sent = loading_end
    update_truck_status(conn, truck_id, 'loading')
    update_truck_status(conn, truck_id, 'on_route')
    delay_minutes = random.randint(0, 60)
    delivery_delay = timedelta(minutes=delay_minutes)
    actual_return_time = estimated_return_time + delivery_delay
    delivered_dict = {}
    total_cost = 0
    for item in products:
        pellet_ids = mark_product_pellets_as_sent(conn, item['product_id'], item['quantity'], current_date)
        delivered_dict[str(item['product_id'])] = pellet_ids
        total_cost += get_pallet_cost(conn, item['product_id']) * item['quantity']
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO inventory_delivery (
                store_sent, products_delivered, quantities_delivered, cost,
                truck_sent, driver_sent, time_sent, status, date_time, quantity
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'scheduled', %s, %s)
            RETURNING transaction_id;
        """, (
            store_id,
            json.dumps(delivered_dict),
            json.dumps([item['quantity'] for item in products]),
            total_cost,
            truck_id,
            driver_id,
            time_sent,
            current_date,
            sum(item['quantity'] for item in products)
        ))
        delivery_id = cur.fetchone()[0]
        cur.execute("""
            UPDATE inventory_delivery
            SET status = 'completed', time_returned = %s
            WHERE transaction_id = %s;
        """, (actual_return_time, delivery_id))
    conn.commit()
    log_transaction(conn, total_cost, 'delivery', current_date)
    # Only log anomalies if delay exceeds 30 minutes.
    if delivery_delay > timedelta(minutes=30):
        log_delivery_anomalies(
            conn,
            transaction_id=delivery_id,
            expected_cost=total_cost,
            actual_cost=total_cost,
            driver_id=driver_id,
            delivery_start=now_dt,
            delivery_end=actual_return_time,
            current_date=current_date,
            delivery_id=delivery_id  # New parameter for underperformance_log.
        )
    store_distance = get_store_distance(conn, store_id)
    km_driven_delivery = store_distance * 2
    extra_km = round(random.uniform(0, 5), 2) if delay_minutes > 0 else 0
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO truck_log (
                delivery_id, driver_id, time_sent, time_returned, expected_time,
                status, distance_km, km_driven_delivery, extra_km, delivery_delay, date_time
            ) VALUES (%s, %s, %s, %s, %s, 'on_time', %s, %s, %s, %s, %s);
        """, (
            delivery_id,
            driver_id,
            time_sent,
            actual_return_time,
            store_expected_time,
            get_store_distance(conn, store_id),
            km_driven_delivery,
            extra_km,
            delivery_delay,
            current_date
        ))
    conn.commit()
    refuel_truck_after_delivery(conn, truck_id, driver_id, km_driven_delivery, current_date)
    update_truck_status(conn, truck_id, 'available')

# --- Refuel Truck After Delivery ---
def refuel_truck_after_delivery(conn, truck_id, driver_id, km_driven, current_date):
    gas_price = get_current_gas_price(conn)
    liters_used = km_driven / 3.0
    cost = round(liters_used * gas_price, 2)
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO transactions (type, cost, date, date_time)
            VALUES ('fuel', %s, %s, %s)
            RETURNING transaction_id;
        """, (cost, current_date, current_date))
        transaction_id = cur.fetchone()[0]
        cur.execute("""
            INSERT INTO fuel_log (transaction_id, truck_id, employee_id, cost, liters, cost_per_liter, expected_cost, date_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """, (transaction_id, truck_id, driver_id, cost, liters_used, gas_price, cost, current_date))
    conn.commit()

# if __name__ == "__main__":
#     fulfill_orders(datetime.now().date())
