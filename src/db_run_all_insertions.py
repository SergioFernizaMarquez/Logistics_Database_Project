import os
import psycopg2
import pandas as pd
from db_inserter import (
    insert_employees,
    insert_trucks,
    insert_stores,
    insert_product_pellets,
    insert_product_pellet,
    insert_suppliers,
    insert_inventory
)

# Define paths to all CSV files
DATA_FOLDER = "generated_data"

paths = {
    "employees": os.path.join(DATA_FOLDER, "employees.csv"),
    "trucks": os.path.join(DATA_FOLDER, "trucks.csv"),
    "stores": os.path.join(DATA_FOLDER, "stores.csv"),
    "product_pellets": os.path.join(DATA_FOLDER, "product_pellets.csv"),
    "product_pellet": os.path.join(DATA_FOLDER, "product_pellet.csv"),
    "suppliers": os.path.join(DATA_FOLDER, "suppliers.csv"),
    "inventory": os.path.join(DATA_FOLDER, "inventory.csv")
}

def get_db_connection():
    return psycopg2.connect(
        dbname="db_logistics",
        user="sergio",
        password="serfermar",
        host="localhost",
        port="5432"
    )

def run_all_insertions():
    conn = get_db_connection()

    print("Inserting employees...")
    df = pd.read_csv(paths["employees"])
    insert_employees(conn, df)

    print("Inserting trucks...")
    df = pd.read_csv(paths["trucks"])
    insert_trucks(conn, df)

    print("Inserting stores...")
    df = pd.read_csv(paths["stores"])
    insert_stores(conn, df)

    print("Inserting product pellets summary...")
    df = pd.read_csv(paths["product_pellets"])
    insert_product_pellets(conn, df)

    print("Inserting individual product pellets...")
    df = pd.read_csv(paths["product_pellet"])
    insert_product_pellet(conn, df)

    print("Inserting suppliers...")
    df = pd.read_csv(paths["suppliers"])
    insert_suppliers(conn, df)

    print("Inserting inventory...")
    df = pd.read_csv(paths["inventory"])
    insert_inventory(conn, df)

    conn.close()
    print("All data inserted successfully.")

if __name__ == "__main__":
    run_all_insertions()
