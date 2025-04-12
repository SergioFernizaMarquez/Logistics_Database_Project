import pandas as pd
import random
import string
import os
from datetime import timedelta

# Ensure output directory exists
DATA_DIR = "generated_data"
os.makedirs(DATA_DIR, exist_ok=True)

# Load product data
product_df = pd.read_csv(os.path.join(DATA_DIR, 'product_pellets.csv'))

# Function to generate a random alphanumeric supplier ID
def generate_supplier_id(existing_ids, length=8):
    while True:
        sid = ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        if sid not in existing_ids:
            return sid

# Create suppliers (shared across products)
unique_supplier_ids = []
supplier_records = []

for _, row in product_df.iterrows():
    product_id = row['product_id']
    product_category = row['category']

    # Randomly reuse a supplier_id or generate a new one (80% chance of reuse)
    if unique_supplier_ids and random.random() < 0.8:
        supplier_id = random.choice(unique_supplier_ids)
    else:
        supplier_id = generate_supplier_id(unique_supplier_ids)
        unique_supplier_ids.append(supplier_id)

    # Generate delivery time between 3 and 6 hours
    hours = random.randint(3, 6)
    expected_delivery_time = str(timedelta(hours=hours))

    supplier_records.append({
        'supplier_id': supplier_id,
        'product_id': product_id,
        'product_category': product_category,
        'expected_delivery_time': expected_delivery_time
    })

# Create DataFrame and save
supplier_df = pd.DataFrame(supplier_records)
supplier_df.to_csv(os.path.join(DATA_DIR, 'suppliers.csv'), index=False)
