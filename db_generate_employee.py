import pandas as pd
import random
import string
from faker import Faker
from cryptography.fernet import Fernet
import base64
import hashlib
from datetime import datetime
import numpy as np
import os

# Initialize Faker and constants
fake = Faker()
Faker.seed(0)
random.seed(0)
np.random.seed(0)

# Job roles, counts, salaries (mean), and std deviation
roles = [
    ("driver", 10, 6000),
    ("forklift_operator", 5, 4000),
    ("warehouse_worker", 15, 9000),
    ("admin", 2, 5000),
    ("security", 5, 3000),
    ("cleaning", 5, 7000),
    ("maintenance", 3, 7000)
]

# Key derivation function (from passphrase)
def derive_key_from_passphrase(passphrase: str) -> bytes:
    return base64.urlsafe_b64encode(
        hashlib.sha256(passphrase.encode()).digest()
    )

# Encryption setup
passphrase = "sample_admin_key"
key = derive_key_from_passphrase(passphrase)
fernet = Fernet(key)

# Generate employee data
employees = []
employee_id = 1

for role, count, salary_mean in roles:
    for _ in range(count):
        name = fake.unique.name()
        phone = f"+1-{fake.msisdn()[0:3]}-{fake.msisdn()[3:6]}-{fake.msisdn()[6:10]}"
        salary = round(np.random.normal(loc=salary_mean, scale=1000), 2)
        acc_num = ''.join(random.choices(string.digits, k=12))
        encrypted_acc = fernet.encrypt(acc_num.encode()).decode()
        hours_week = max(0, int(np.random.normal(40, 6)))  # no negative hours
        employees.append([
            employee_id, name, phone, role, salary,
            encrypted_acc, hours_week
        ])
        employee_id += 1

# Create DataFrame and export
df = pd.DataFrame(employees, columns=[
    "employee_id", "name", "phone_num", "job_role",
    "salary", "account_num", "hours_week"
])

# Ensure output folder exists
output_dir = "generated_data"
os.makedirs(output_dir, exist_ok=True)

# Save to local folder
csv_path = os.path.join(output_dir, "employees.csv")
df.to_csv(csv_path, index=False)
