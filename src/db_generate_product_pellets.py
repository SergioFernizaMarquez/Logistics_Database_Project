import random
import pandas as pd
import os

# Ensure the output directory exists
DATA_DIR = "generated_data"
os.makedirs(DATA_DIR, exist_ok=True)

product_data = []
total_quantity = 0
max_total = 25000

all_products = [
    ("Whole Milk", "Dairy"),
    ("2% Milk", "Dairy"),
    ("Lactose-Free Milk", "Dairy"),
    ("Cheddar Cheese", "Dairy"),
    ("Mozzarella Cheese", "Dairy"),
    ("Yogurt Cups", "Dairy"),
    ("Greek Yogurt", "Dairy"),
    ("Parmesan", "Dairy"),
    ("Butter", "Dairy"),
    ("Cream Cheese", "Dairy"),

    ("Romaine Lettuce", "Produce"),
    ("Baby Spinach", "Produce"),
    ("Tomatoes", "Produce"),
    ("Cucumbers", "Produce"),
    ("Carrots", "Produce"),
    ("Potatoes", "Produce"),
    ("Onions", "Produce"),
    ("Apples", "Produce"),
    ("Bananas", "Produce"),
    ("Oranges", "Produce"),

    ("Ground Beef", "Meat"),
    ("Chicken Breast", "Meat"),
    ("Pork Chops", "Meat"),
    ("Bacon", "Meat"),
    ("Sausage Links", "Meat"),
    ("Ham Slices", "Meat"),
    ("Salmon Fillet", "Meat"),
    ("Tilapia", "Meat"),
    ("Shrimp (Frozen)", "Meat"),
    ("Turkey Ground", "Meat"),

    ("Pasta", "Pantry"),
    ("White Rice", "Pantry"),
    ("Brown Rice", "Pantry"),
    ("All-purpose Flour", "Pantry"),
    ("Sugar", "Pantry"),
    ("Salt", "Pantry"),
    ("Olive Oil", "Pantry"),
    ("Vegetable Oil", "Pantry"),
    ("Canned Beans", "Pantry"),
    ("Peanut Butter", "Pantry"),

    ("Toilet Paper", "Household"),
    ("Paper Towels", "Household"),
    ("Dish Soap", "Household"),
    ("Laundry Detergent", "Household"),
    ("Trash Bags", "Household"),
    ("Bleach", "Household"),
    ("Sponges", "Household"),
    ("Aluminum Foil", "Household"),
    ("Plastic Wrap", "Household"),
    ("Disinfectant Wipes", "Household")
]

for product_name, category in all_products:
    if len(product_data) >= 50:
        break
    max_remaining = max_total - total_quantity
    if max_remaining <= 0:
        break

    quantity_min = 100
    quantity_max = min(1000, max_remaining)
    if quantity_min > quantity_max:
        quantity = quantity_max
    else:
        quantity = random.randint(quantity_min, quantity_max)

    product_data.append({
        "product_id": len(product_data) + 1,
        "name": product_name,
        "category": category,
        "quantity": quantity,
        "pallet_cost": round(random.uniform(40, 200), 2)
    })
    total_quantity += quantity

df_products = pd.DataFrame(product_data)
df_products.to_csv(os.path.join(DATA_DIR, "product_pellets.csv"), index=False)
