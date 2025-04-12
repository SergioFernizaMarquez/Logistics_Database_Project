import pandas as pd
import random
import uuid
import os
from datetime import datetime, timedelta
import json

# Directory setup
output_dir = "generated_data"
os.makedirs(output_dir, exist_ok=True)

# Load product and store data
products_df = pd.read_csv(os.path.join(output_dir, 'product_pellets.csv'))
stores_df = pd.read_csv(os.path.join(output_dir, 'stores.csv'))

# Generate a fake product entry for a pending order
def make_product_entry(product):
    quantity = random.randint(1, 10)
    weight_per_unit = round(random.uniform(20.0, 50.0), 2)
    refrigerated = random.choice([True, False])
    return {
        "product_id": int(product["product_id"]),
        "quantity": quantity,
        "weight": weight_per_unit,
        "refrigerated": refrigerated
    }

# Generate 10 pending orders
pending_orders = []
for _ in range(10):
    store = stores_df.sample(1).iloc[0]
    store_id = store['store_id']
    
    num_products = random.randint(1, 3)
    selected_products = products_df.sample(num_products)

    products = [make_product_entry(prod) for _, prod in selected_products.iterrows()]
    
    order = {
        "store_id": store_id,
        "products": json.dumps(products),
        "date_time": (datetime.now() - timedelta(days=random.randint(0, 2))).strftime("%Y-%m-%d %H:%M:%S")
    }
    pending_orders.append(order)

# Save to CSV
pending_orders_df = pd.DataFrame(pending_orders)
pending_orders_df.to_csv(os.path.join(output_dir, "pending_orders.csv"), index=False)
