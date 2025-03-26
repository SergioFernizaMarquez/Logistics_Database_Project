import psycopg2
from datetime import datetime
from db_order_anomaly_log import log_overspending

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
            ) VALUES (%s, 'payroll', %s, %s, %s);
        """, (transaction_id, cost, now.date(), now))
    conn.commit()

# --- Check for Duplicate Payroll ---
def payroll_already_logged(conn, employee_id):
    now = datetime.now()
    start_of_month = now.replace(day=1)
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 1 FROM payroll_log
            WHERE employee_id = %s AND date_time >= %s
        """, (employee_id, start_of_month))
        return cur.fetchone() is not None

# --- Fetch Expected Payroll ---
def get_expected_salary(conn, employee_id):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT salary FROM employee
            WHERE employee_id = %s
        """, (employee_id,))
        result = cur.fetchone()
        return result[0] if result else None

# --- Add Payroll Entry ---
def add_payroll_log(employee_id, payment, account_num, last_payment, next_payment):
    conn = get_db_connection()
    now = datetime.now()
    with conn:
        if payroll_already_logged(conn, employee_id):
            print(f"Payroll already registered for employee {employee_id} this month.")
            return

        expected_salary = get_expected_salary(conn, employee_id)

        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO payroll_log (
                    employee_id, payment, account_num,
                    last_payment, next_payment, date_time
                ) VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING transaction_id;
            """, (employee_id, payment, account_num, last_payment, next_payment, now))
            transaction_id = cur.fetchone()[0]

            log_transaction(conn, transaction_id, payment)
            if expected_salary:
                log_overspending(conn, transaction_id, expected_salary, payment, employee_id)

if __name__ == "__main__":
    add_payroll_log()
