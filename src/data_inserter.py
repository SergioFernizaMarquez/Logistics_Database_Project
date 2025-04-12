
import psycopg2
import pandas as pd

def insert_employees(conn, employee_df):
    with conn.cursor() as cur:
        for _, row in employee_df.iterrows():
            cur.execute("""
                INSERT INTO employee (
                    employee_id, name, phone_num, job_role, salary,
                    account_num, hours_week
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                row['employee_id'], row['name'], row['phone_num'],
                row['job_role'], row['salary'], row['account_num'],
                row['hours_week']
            ))
    conn.commit()

def insert_stores(conn, store_df):
    with conn.cursor() as cur:
        for _, row in store_df.iterrows():
            cur.execute("""
                INSERT INTO store (
                    store_id, name, address, distance_km,
                    expected_time, open_time, close_time
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                row['store_id'], row['name'], row['address'], row['distance_km'],
                row['expected_time'], row['open_time'], row['close_time']
            ))
    conn.commit()

def insert_product_pellets(conn, product_df):
    with conn.cursor() as cur:
        for _, row in product_df.iterrows():
            cur.execute("""
                INSERT INTO product_pellets (
                    product_id, name, category, quantity, pallet_cost
                ) VALUES (%s, %s, %s, %s, %s)
            """, (
                row['product_id'], row['name'], row['category'],
                row['quantity'], row['pallet_cost']
            ))
    conn.commit()

def insert_product_pellet(conn, pellet_df):
    with conn.cursor() as cur:
        for _, row in pellet_df.iterrows():
            cur.execute("""
                INSERT INTO product_pellet (
                    pellet_id, name, category, cost, weight,
                    received, sell_by, refrigerated, sent
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                row['pellet_id'], row['name'], row['category'], row['cost'],
                row['weight'], row['received'], row['sell_by'],
                row['refrigerated'], row['sent']
            ))
    conn.commit()

def insert_trucks(conn, truck_df):
    with conn.cursor() as cur:
        for _, row in truck_df.iterrows():
            cur.execute("""
                INSERT INTO truck (
                    truck_id, employee_id, plate_number, refrigerated,
                    capacity, km_driven, operational_status,
                    fuel_capacity, last_maintanance
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                row['truck_id'], row['employee_id'], row['plate_number'],
                row['refrigerated'], row['capacity'], row['km_driven'],
                row['operational_status'], row['fuel_capacity'],
                row['last_maintanance']
            ))
    conn.commit()

def insert_suppliers(conn, supplier_df):
    with conn.cursor() as cur:
        for _, row in supplier_df.iterrows():
            cur.execute("""
                INSERT INTO supplier (
                    supplier_id, expected_delivery_time,
                    product_id, product_category
                ) VALUES (%s, %s, %s, %s)
            """, (
                row['supplier_id'], row['expected_delivery_time'],
                row['product_id'], row['product_category']
            ))
    conn.commit()

def insert_forklifts(conn, forklift_df):
    with conn.cursor() as cur:
        for _, row in forklift_df.iterrows():
            cur.execute("""
                INSERT INTO forklift (
                    forklift_id, employee_id, operational_status,
                    last_maintanance, unloading_time_pellet
                ) VALUES (%s, %s, %s, %s, %s)
            """, (
                row['forklift_id'], row['employee_id'], row['operational_status'],
                row['last_maintanance'], row['unloading_time_pellet']
            ))
    conn.commit()

def insert_inventory(conn, inventory_df):
    with conn.cursor() as cur:
        for _, row in inventory_df.iterrows():
            cur.execute("""
                INSERT INTO inventory (
                    inventory_id, capacity_pellets, current_pellets,
                    to_be_sent, to_be_received
                ) VALUES (%s, %s, %s, %s, %s)
            """, (
                row['inventory_id'], row['capacity_pellets'], row['current_pellets'],
                row['to_be_sent'], row['to_be_received']
            ))
    conn.commit()
