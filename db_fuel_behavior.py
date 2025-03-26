import psycopg2
from datetime import datetime

# --- Database Connection Helper ---
def get_db_connection():
    return psycopg2.connect(
        dbname="your_db_name",
        user="your_username",
        password="your_password",
        host="localhost",
        port="5432"
    )

# --- Log to Transactions Table ---
def log_transaction(conn, transaction_id, cost):
    now = datetime.now()
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO transactions (
                transaction_id, type, cost, date, date_time
            ) VALUES (%s, 'fuel', %s, %s, %s);
        """, (transaction_id, cost, now.date(), now))
    conn.commit()

# --- Check for Duplicate Fuel Log This Month ---
def fuel_log_exists_this_month(conn, truck_id):
    now = datetime.now()
    start_of_month = now.replace(day=1)
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 1 FROM fuel_log
            WHERE truck_id = %s AND date_time >= %s
        """, (truck_id, start_of_month))
        return cur.fetchone() is not None

# --- Log to Overspending Table ---
def detect_fuel_overspending(conn, transaction_id, actual_cost, expected_cost, employee_id):
    if actual_cost > expected_cost * 1.10:
        deviation = actual_cost - expected_cost
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO overspending_log (
                    transaction_id, type, expected_cost, actual_cost,
                    deviation, reason, flagged_by, date_time, employee_id
                ) VALUES (%s, 'fuel', %s, %s, %s, %s, 'system', NOW());
            """, (
                transaction_id,
                expected_cost,
                actual_cost,
                deviation,
                'Fuel cost exceeded expected threshold',
                employee_id
            ))
        conn.commit()

# --- Add Fuel Log Entry ---
def add_fuel_log(truck_id, employee_id, cost, liters, cost_per_liter, expected_cost):
    conn = get_db_connection()
    now = datetime.now()
    with conn:
        if fuel_log_exists_this_month(conn, truck_id):
            print(f"Fuel already logged for truck {truck_id} this month.")
            return

        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO fuel_log (
                    truck_id, employee_id, cost, liters, cost_per_liter, expected_cost, date_time
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING transaction_id;
            """, (truck_id, employee_id, cost, liters, cost_per_liter, expected_cost, now))
            transaction_id = cur.fetchone()[0]
            
            log_transaction(conn, transaction_id, cost)
            detect_fuel_overspending(conn, transaction_id, cost, expected_cost)

if __name__ == "__main__":
    add_fuel_log()
