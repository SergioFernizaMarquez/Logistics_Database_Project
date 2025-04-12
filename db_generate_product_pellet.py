import pandas as pd
import random
from datetime import datetime, timedelta
import os

# Set data directory
DATA_DIR = "generated_data"
os.makedirs(DATA_DIR, exist_ok=True)

# Load product summary data
product_df = pd.read_csv(os.path.join(DATA_DIR, "product_pellets.csv"))

# Helper functions
def random_received_date():
    days_ago = random.randint(1, 60)
    return datetime.now() - timedelta(days=days_ago)

def random_sell_by_date(received):
    return received + timedelta(days=random.randint(10, 45))

def generate_pellets_from_product(product_row):
    product_name = product_row["name"]
    category = product_row["category"]
    total_quantity = product_row["quantity"]
    cost = product_row["pallet_cost"]

    remaining_quantity = total_quantity
    entries = []

    while remaining_quantity > 0:
        quantity = min(remaining_quantity, random.randint(1, 3))
        weight = round(random.uniform(200.0, 400.0), 2)
        received_date = random_received_date()
        sell_by = random_sell_by_date(received_date)
        refrigerated = category.lower() in ["dairy", "meat", "frozen", "produce"]
        sent = False

        entries.append({
            "name": product_name,
            "category": category,
            "cost": cost,
            "weight": weight,
            "received": received_date.date(),
            "sell_by": sell_by.date(),
            "refrigerated": refrigerated,
            "sent": sent
        })

        remaining_quantity -= quantity

    return entries

# Generate all entries
all_pellets = []
for _, row in product_df.iterrows():
    pellets = generate_pellets_from_product(row)
    all_pellets.extend(pellets)

# Create DataFrame
pellets_df = pd.DataFrame(all_pellets)
pellets_df.index += 1
pellets_df.index.name = "pellet_id"

# Save to CSV
pellets_df.to_csv(os.path.join(DATA_DIR, "product_pellet.csv"))
