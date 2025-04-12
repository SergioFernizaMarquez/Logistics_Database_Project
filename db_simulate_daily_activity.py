from datetime import datetime, timedelta
import random
from db_config import get_db_connection
from db_payroll_behavior import process_payrolls
from db_order_behavior import fulfill_orders, request_resupply, get_inventory_status, update_truck_status
from db_restock_behavior import unload_supplier_deliveries

def reset_product_pellet_sequence(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT MAX(pellet_id) FROM product_pellet;")
        max_val = cur.fetchone()[0]
        if max_val is None:
            max_val = 0
        cur.execute("SELECT setval(pg_get_serial_sequence('product_pellet', 'pellet_id'), %s, true);", (max_val,))
    conn.commit()

def reset_trucks_from_previous_maintenance(current_date):
    """
    For trucks whose operational_status is 'maintenance' from yesterday,
    update their status to 'available' (leaving last_maintanance as yesterday).
    """
    conn = get_db_connection()
    yesterday = current_date - timedelta(days=1)
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE truck
            SET operational_status = 'available'
            WHERE operational_status = 'maintenance' AND last_maintanance = %s;
        """, (yesterday,))
    conn.commit()
    conn.close()

def get_current_gas_price(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT value FROM system_config WHERE key = 'current_gas_price';")
        result = cur.fetchone()
        return float(result[0]) if result is not None and result[0] is not None else 3.0

def update_gas_price(conn):
    current_price = get_current_gas_price(conn)
    multiplier = random.uniform(0.99, 1.01)
    new_price = round(current_price * multiplier, 3)
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO system_config (key, value)
            VALUES ('current_gas_price', %s)
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;
        """, (new_price,))
    conn.commit()

def discard_expired_products(current_date):
    conn = get_db_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM product_pellet
                WHERE sell_by IS NOT NULL AND sell_by < %s AND sent = FALSE;
            """, (current_date,))
            count = cur.fetchone()[0]
            if count > 0:
                print(f"{count} expired products removed from inventory on {current_date}")
            cur.execute("""
                DELETE FROM product_pellet
                WHERE sell_by IS NOT NULL AND sell_by < %s AND sent = FALSE;
            """, (current_date,))
    conn.commit()

def check_all_trucks_maintenance(current_date):
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT truck_id, last_maintanance FROM truck;")
        trucks = cur.fetchall()
        for truck_id, last_maintanance in trucks:
            if last_maintanance is not None and (current_date - last_maintanance).days >= 200:
                cur.execute("""
                    UPDATE truck
                    SET operational_status = 'maintenance',
                        last_maintanance = %s
                    WHERE truck_id = %s;
                """, (current_date, truck_id))
    conn.commit()

def auto_restock_low_inventory(current_date):
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT product_id FROM product_pellets;")
        product_ids = [row[0] for row in cur.fetchall()]
    for product_id in product_ids:
        current, _, incoming, capacity = get_inventory_status(conn, product_id)
        if current < 300:
            needed = 500 - current
            request_resupply(conn, product_id, needed, current_date)
    conn.commit()

def refill_truck_fuel(current_date):
    from db_fuel_behavior import add_fuel_log
    conn = get_db_connection()
    gas_price = get_current_gas_price(conn)
    with conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT truck_id, fuel_capacity, km_driven FROM truck
                WHERE operational_status = 'available';
            """)
            for truck_id, capacity, km_driven in cur.fetchall():
                cur.execute("SELECT SUM(liters) FROM fuel_log WHERE truck_id = %s;", (truck_id,))
                filled = cur.fetchone()[0] or 0
                fuel_level = filled % capacity
                # Refuel if fuel is less than 25% of capacity, without monthly constraint.
                if fuel_level / capacity < 0.25:
                    refill = random.uniform(capacity * 0.5, capacity - fuel_level)
                    cost = round(refill * gas_price, 2)
                    add_fuel_log(truck_id, 1, cost, refill, gas_price, cost, current_date)
    conn.commit()

def reset_available_trucks(current_date):
    conn = get_db_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE truck
                SET operational_status = 'available'
                WHERE truck_id IN (
                    SELECT truck_sent FROM inventory_delivery
                    WHERE time_returned <= %s
                )
            """, (datetime.combine(current_date, datetime.max.time()),))
    conn.commit()

def place_new_orders(current_date):
    import json
    conn = get_db_connection()
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT store_id FROM store;")
            store_ids = [r[0] for r in cur.fetchall()]
            cur.execute("SELECT product_id, pallet_cost FROM product_pellets;")
            products = cur.fetchall()
            order_count = random.randint(10, 20)
            for _ in range(order_count):
                store_id = random.choice(store_ids)
                num_products = random.randint(1, 3)
                selected = random.sample(products, num_products)
                total_qty = 0
                items = []
                for prod_id, cost in selected:
                    max_qty = min(150 - total_qty, random.randint(10, 80))
                    if max_qty <= 0:
                        break
                    qty = random.randint(1, max_qty)
                    total_qty += qty
                    items.append({
                        "product_id": prod_id,
                        "quantity": qty,
                        "weight": random.uniform(20.0, 50.0),
                        "refrigerated": False
                    })
                if items:
                    cur.execute("""
                        INSERT INTO pending_orders (store_id, products, date_time)
                        VALUES (%s, %s, %s);
                    """, (store_id, json.dumps(items), current_date))
    conn.commit()

def simulate_daily_activities(current_date):
    # Reset product_pellet sequence to avoid duplicate key errors.
    conn = get_db_connection()
    reset_product_pellet_sequence(conn)
    conn.close()
    
    # Reset trucks from previous day maintenance.
    reset_trucks_from_previous_maintenance(current_date)
    
    discard_expired_products(current_date)
    auto_restock_low_inventory(current_date)
    update_gas_price(get_db_connection())
    process_payrolls(current_date)
    reset_available_trucks(current_date)
    refill_truck_fuel(current_date)
    check_all_trucks_maintenance(current_date)
    place_new_orders(current_date)
    unload_supplier_deliveries(current_date)  # Process restock orders.
    fulfill_orders(current_date)
    
if __name__ == "__main__":
    simulate_daily_activities(datetime.now().date())
