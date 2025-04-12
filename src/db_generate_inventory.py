import pandas as pd
import os

# Ensure output folder exists
output_dir = "generated_data"
os.makedirs(output_dir, exist_ok=True)

# Load product_pellets.csv
product_df = pd.read_csv(os.path.join(output_dir, 'product_pellets.csv'))

# Compute current_pellets from total quantity
current_pellets = product_df['quantity'].sum()

# Set capacity at 25000
capacity_pellets = 25000

# to_be_sent and to_be_received are 0 initially
to_be_sent = 0
to_be_received = 0

# Create DataFrame
inventory_df = pd.DataFrame([{
    'inventory_id': 1,
    'capacity_pellets': capacity_pellets,
    'current_pellets': current_pellets,
    'to_be_sent': to_be_sent,
    'to_be_received': to_be_received
}])

# Save to CSV
inventory_df.to_csv(os.path.join(output_dir, 'inventory.csv'), index=False)
