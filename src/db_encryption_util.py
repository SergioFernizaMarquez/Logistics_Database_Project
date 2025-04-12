from cryptography.fernet import Fernet
import psycopg2
from datetime import datetime
from db_payroll_behavior import log_transaction

# --- Load or define encryption key ---
# In real-world use, this key should be stored securely, not hardcoded.
ENCRYPTION_KEY = b'sample_admin_key__must_be_32_bytes!'
fernet = Fernet(Fernet.generate_key())

# --- Encryption Utility ---
def encrypt_account_number(account_number: str) -> str:
    return fernet.encrypt(account_number.encode()).decode()

# --- Decryption Utility ---
def decrypt_account_number(encrypted_account: str) -> str:
    return fernet.decrypt(encrypted_account.encode()).decode()

# --- Simulate Transaction to External Bank ---
def simulate_bank_transfer(employee_id, payment, decrypted_account_num):
    print(f"Simulating bank transfer:")
    print(f"  - Employee ID: {employee_id}")
    print(f"  - Payment Amount: ${payment:.2f}")
    print(f"  - Destination Account: {decrypted_account_num}")
    print("  - Status: SUCCESS\n")

# --- Combined Payroll Operation ---
def execute_payroll_transaction(employee_id, encrypted_account, payment, last_payment, next_payment):
    decrypted_account = decrypt_account_number(encrypted_account)
    simulate_bank_transfer(employee_id, payment, decrypted_account)

    conn = get_db_connection()
    now = datetime.now()
    with conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO payroll_log (
                    employee_id, payment, account_num, last_payment, next_payment, date_time
                ) VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING transaction_id;
            """, (employee_id, payment, encrypted_account, last_payment, next_payment, now))
            transaction_id = cur.fetchone()[0]

        log_transaction(conn, transaction_id, payment)
    conn.commit()

# --- DB Connection (replicating for completeness) ---
def get_db_connection():
    return psycopg2.connect(
        dbname="your_db_name",
        user="your_username",
        password="your_password",
        host="localhost",
        port="5432"
    )
