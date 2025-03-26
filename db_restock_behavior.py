import psycopg2
from datetime import datetime, timedelta
from db_structure import overspending_log, underperformance_log

# --- Database Connection Helper ---
def get_db_connection():
    return psycopg2.connect(
        dbname="your_db_name",
        user="your_username",
        password="your_password",
        host="localhost",
        port="5432"
    )

# --- Get Incoming Deliveries ---
def get_pending_supplier_deliveries(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT transaction_id, supplier_id, product_id, quantity_received, weight, date_time, cost
            FROM supplier_delivery
            WHERE status = 'pending'
            ORDER BY date_time ASC;
        """)
        return cur.fetchall()

# --- Get Warehouse Capacity ---
def get_warehouse_space(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT capacity_pellets, current_pellets, to_be_received
            FROM inventory
            WHERE inventory_id = 1;
        """)
        return cur.fetchone()

# --- Log Unloading Queue ---
def log_unloading_queue(conn, truck_id, employee_id, quantity):
    now = datetime.now()
    start = now
    end = now + timedelta(minutes=30)
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO unloading_queue (
                forklift_id, employee_id, expected_time,
                start_time, finalized_time, quantity, truck_id, date_time
            ) VALUES (
                1, %s, INTERVAL '30 minutes', %s, %s, %s, %s, %s
            );
        """, (employee_id, start, end, quantity, truck_id, now))
    conn.commit()
    return start, end

# --- Log to Transactions Table ---
def log_transaction(conn, transaction_id, cost):
    now = datetime.now()
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO transactions (
                transaction_id, type, cost, date, date_time
            ) VALUES (%s, 'supplier_delivery', %s, %s, %s);
        """, (transaction_id, cost, now.date(), now))
    conn.commit()

# --- Update Inventory and Mark Delivery Complete ---
def process_delivery(conn, delivery_id, product_id, quantity, cost):
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE inventory
            SET current_pellets = current_pellets + %s,
                to_be_received = to_be_received - %s
            WHERE inventory_id = 1;
        """, (quantity, quantity))

        cur.execute("""
            UPDATE supplier_delivery
            SET status = 'received', order_received = %s
            WHERE transaction_id = %s;
        """, (datetime.now(), delivery_id))

    log_transaction(conn, delivery_id, cost)
    conn.commit()

# --- Unloading Engine ---
def unload_supplier_deliveries():
    conn = get_db_connection()
    with conn:
        deliveries = get_pending_supplier_deliveries(conn)
        for delivery_id, supplier_id, product_id, quantity, weight, created_time, cost in deliveries:
            capacity, current, incoming = get_warehouse_space(conn)
            available_space = capacity - current

            if available_space < quantity:
                print(f"Skipping delivery {delivery_id}, not enough space.")
                continue

            employee_id = 1
            truck_id = 1

            start_time, end_time = log_unloading_queue(conn, truck_id, employee_id, quantity)
            process_delivery(conn, delivery_id, product_id, quantity, cost)

            # Overspending log (mock expected cost = quantity * 2.5 for demo)
            expected_cost = quantity * 2.5
            log_overspending(conn, delivery_id, expected_cost, cost, employee_id)

            # Underperformance log for unloading delay
            expected_duration = timedelta(minutes=30)
            actual_duration = end_time - start_time
            log_underperformance(conn, 'forklift', employee_id, 'unloading_delay', expected_duration, actual_duration)

if __name__ == "__main__":
    unload_supplier_deliveries()
