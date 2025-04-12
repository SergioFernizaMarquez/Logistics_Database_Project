from datetime import datetime
from db_config import get_db_connection

# --- Log to Transactions Table ---
def log_transaction(conn, cost, current_date):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO transactions (
                type, cost, date, date_time
            ) VALUES ('fuel', %s, %s, %s)
            RETURNING transaction_id;
        """, (cost, current_date, current_date))
        return cur.fetchone()[0]

# --- Check for Duplicate Fuel Log This Month ---
def fuel_log_exists_this_month(conn, truck_id, current_date):
    start_of_month = current_date.replace(day=1)
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 1 FROM fuel_log
            WHERE truck_id = %s AND date_time >= %s
        """, (truck_id, start_of_month))
        return cur.fetchone() is not None

# --- Log to Overspending Table ---
def detect_fuel_overspending(conn, transaction_id, actual_cost, expected_cost, employee_id, current_date):
    if actual_cost > expected_cost * 1.10:
        deviation = actual_cost - expected_cost
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO overspending_log (
                    transaction_id, type, expected_cost, actual_cost,
                    deviation, reason, flagged_by, date_time, employee_id
                ) VALUES (%s, 'fuel', %s, %s, %s, %s, 'system', %s, %s);
            """, (
                transaction_id,
                expected_cost,
                actual_cost,
                deviation,
                'Fuel cost exceeded expected threshold',
                current_date,
                employee_id
            ))
        conn.commit()

# --- Add Fuel Log Entry ---
def add_fuel_log(truck_id, employee_id, cost, liters, cost_per_liter, expected_cost, current_date):
    conn = get_db_connection()
    with conn:

        transaction_id = log_transaction(conn, cost, current_date)

        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO fuel_log (
                    transaction_id, truck_id, employee_id, cost, liters, cost_per_liter, expected_cost, date_time
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """, (
                transaction_id,
                truck_id,
                employee_id,
                cost,
                liters,
                cost_per_liter,
                expected_cost,
                current_date
            ))

        detect_fuel_overspending(conn, transaction_id, cost, expected_cost, employee_id, current_date)
        conn.commit()

# if __name__ == "__main__":
#     add_fuel_log()
