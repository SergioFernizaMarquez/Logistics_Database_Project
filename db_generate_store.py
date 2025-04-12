import pandas as pd
import random
import string
import numpy as np
from datetime import timedelta
import math
import os

# Output directory
DATA_DIR = "generated_data"
os.makedirs(DATA_DIR, exist_ok=True)

# Neighborhood and store name lists
neighborhoods = [
    "Downtown", "Greenville", "Hilltop", "Maplewood", "Oakridge",
    "Lakeside", "Brookfield", "Sunnydale", "Fairview", "Westfield",
    "Eastbrook", "Riverside", "Meadowpark", "Highland", "Cedar Grove"
]
store_bases = ["FreshMart", "SuperSaver", "DailyMarket", "UrbanGrocer"]

# Helper function to generate random 8-char alphanumeric ID
def generate_store_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# Generate store data
store_data = []
for _ in range(30):
    store_id = generate_store_id()
    store_name = random.choice(store_bases)
    neighborhood = random.choice(neighborhoods)
    full_name = f"{store_name}, {neighborhood}"

    street_type = random.choice(["Ave", "St", "Blvd"])
    street_number = random.randint(100, 999)
    zip_code = random.randint(10000, 99999)
    address = f"{street_number} {neighborhood} {street_type}, {zip_code}"

    distance_km = round(random.uniform(1, 50), 2)
    speed_kph = random.randint(20, 60)
    expected_minutes = math.ceil((distance_km / speed_kph) * 60)
    expected_time = timedelta(minutes=expected_minutes)

    open_time = "08:00"
    close_time = "22:00"

    store_data.append({
        "store_id": store_id,
        "name": full_name,
        "address": address,
        "distance_km": distance_km,
        "expected_time": str(expected_time),
        "open_time": open_time,
        "close_time": close_time
    })

store_df = pd.DataFrame(store_data)
store_df.to_csv(os.path.join(DATA_DIR, "stores.csv"), index=False)
