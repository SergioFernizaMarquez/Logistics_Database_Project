import pandas as pd
import random
from datetime import datetime, timedelta

# Load employee data and filter drivers
employee_df = pd.read_csv("generated_data/employees.csv")
driver_ids = employee_df[employee_df["job_role"] == "driver"]["employee_id"].tolist()

# Shuffle and pick 10 drivers (or however many you want)
random.shuffle(driver_ids)
driver_ids = driver_ids[:10]

# Helper to generate random plate number
def generate_plate_number():
    letters = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=3))
    numbers = ''.join(random.choices('0123456789', k=4))
    return f"{letters}-{numbers}"

# Generate truck records
truck_data = []
for i in range(len(driver_ids)):
    truck = {
        "employee_id": driver_ids[i],
        "plate_number": generate_plate_number(),
        "refrigerated": i < 5,
        "capacity": round(random.uniform(5000, 10000), 2),
        "km_driven": round(random.uniform(0, 50000), 2),
        "operational_status": "available",
        "fuel_capacity": round(random.uniform(200, 400), 2),
        "last_maintanance": (datetime.now() - timedelta(days=random.randint(0, 365))).date()
    }
    truck_data.append(truck)

truck_df = pd.DataFrame(truck_data)
truck_df.to_csv("generated_data/trucks.csv", index=False)
