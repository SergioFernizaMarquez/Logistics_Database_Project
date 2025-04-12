from datetime import datetime, timedelta
from db_order_anomaly_log import log_overspending
from db_config import get_db_connection

# --- Log to Transactions Table ---
def log_transaction(conn, cost, current_date):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO transactions (
                type, cost, date, date_time
            ) VALUES ('payroll', %s, %s, %s)
            RETURNING transaction_id;
        """, (cost, current_date, current_date))
        return cur.fetchone()[0]

# --- Check for Duplicate Payroll ---
def payroll_already_logged(conn, employee_id, current_date):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 1 FROM payroll_log
            WHERE employee_id = %s
              AND date_trunc('month', date_time) = date_trunc('month', %s)
        """, (employee_id, current_date))
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
def add_payroll_log(conn, employee_id, payment, account_num, last_payment, next_payment, current_date):
    # Use the provided connection instead of opening a new one
    if payroll_already_logged(conn, employee_id, current_date):
        print(f"Payroll already registered for employee {employee_id} this month.")
        return

    expected_salary = get_expected_salary(conn, employee_id)

    # First insert into transactions
    transaction_id = log_transaction(conn, payment, current_date)

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO payroll_log (
                transaction_id, employee_id, payment, account_num,
                last_payment, next_payment, date_time
            ) VALUES (%s, %s, %s, %s, %s, %s, %s);
        """, (
            transaction_id,
            employee_id,
            payment,
            account_num,
            last_payment,
            next_payment,
            current_date
        ))

    if expected_salary:
        log_overspending(conn, transaction_id, expected_salary, payment, employee_id, current_date)

# --- Process Payrolls ---
def process_payrolls(current_date):
    conn = get_db_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT employee_id, salary, account_num, next_payment FROM employee;")
            for emp_id, salary, acc, next_payment in cur.fetchall():
                # Check if payroll is due for this employee
                if next_payment and next_payment <= current_date:
                    add_payroll_log(
                        conn,
                        emp_id,
                        salary,
                        acc,
                        current_date - timedelta(days=30),
                        current_date + timedelta(days=30),
                        current_date
                    )
                    cur.execute("""
                        UPDATE employee
                        SET next_payment = %s
                        WHERE employee_id = %s;
                    """, (current_date + timedelta(days=30), emp_id))
        conn.commit()

# if __name__ == "__main__":
#     # For testing, run process_payrolls with the simulated current date.
#     process_payrolls(datetime.now().date())
