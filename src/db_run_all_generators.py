import os

print("Running all data generators...")

os.system("python3 db_generate_employee.py")
os.system("python3 db_generate_store.py")
os.system("python3 db_generate_truck.py")
os.system("python3 db_generate_product_pellets.py")
os.system("python3 db_generate_product_pellet.py")
os.system("python3 db_generate_supplier.py")
os.system("python3 db_generate_inventory.py")
os.system("python3 db_generate_inventory_delivery.py")

print("All CSVs generated.")
