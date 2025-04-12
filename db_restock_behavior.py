from datetime import datetime, timedelta
from db_config import get_db_connection

# Define a fixed simulation start time (08:00 AM)
SIMULATION_START_TIME = datetime.strptime("08:00", "%H:%M").time()

# --- Get Warehouse Capacity ---
def get_inventory_space(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT capacity_pellets, current_pellets, to_be_received
            FROM inventory
            WHERE inventory_id = 1;
        """)
        return cur.fetchone()

# --- Get Inventory Status ---
def get_inventory_status(conn, product_id):
    """
    Returns four columns from the inventory table:
       current_pellets, to_be_sent, to_be_received, capacity_pellets.
    """
    with conn.cursor() as cur:
        cur.execute("""
            SELECT current_pellets, to_be_sent, to_be_received, capacity_pellets
            FROM inventory
            WHERE inventory_id = 1;
        """)
        return cur.fetchone()

# --- Get Pallet Cost ---
def get_pallet_cost(conn, product_id):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT pallet_cost FROM product_pellets
            WHERE product_id = %s;
        """, (product_id,))
        result = cur.fetchone()
        # Return a float; if NULL, use 0.0
        return float(result[0]) if result is not None and result[0] is not None else 0.0

# --- Get Default Weight ---
def get_product_weight(conn, product_id):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT AVG(weight) FROM product_pellet
            WHERE name = (SELECT name FROM product_pellets WHERE product_id = %s);
        """, (product_id,))
        result = cur.fetchone()
        # Fallback to 30.0
        return float(result[0]) if result is not None and result[0] is not None else 30.0

# --- Unload Supplier Delivery (Single-Product Mode) ---
def unload_supplier_delivery(conn, delivery, current_date):
    """
    Processes a pending supplier delivery for a single product.
    
    Expects a supplier_delivery record with 6 columns:
      (transaction_id, product_id, quantity_received, cost, weight, delivery_date)
    
    Steps:
      1. Mark the supplier_delivery record as 'received'.
      2. Retrieve product details (name, category) from product_pellets.
      3. For each delivered unit, insert one product_pellet record with:
            - cost from get_pallet_cost (unit cost)
            - weight from get_product_weight (unit weight)
            - received = current_date
            - sell_by = current_date + 50 days.
         Collect the returned pellet IDs.
      4. Update the inventory: Increase current_pellets by delivered quantity and 
         decrease to_be_received (clamped at 0).
      5. Log a supplier_delivery transaction with cost calculated as:
               cost = get_pallet_cost(conn, product_id) * quantity.
      6. Return a summary dictionary.
    """
    delivery_id, product_id, quantity, _, weight, _ = delivery
    # Compute cost dynamically.
    computed_cost = get_pallet_cost(conn, product_id) * quantity
    
    with conn.cursor() as cur:
        # Mark delivery as received.
        cur.execute("""
            UPDATE supplier_delivery
            SET status = 'received', order_received = %s
            WHERE transaction_id = %s;
        """, (current_date, delivery_id))
        
        # Retrieve product details.
        cur.execute("""
            SELECT name, category FROM product_pellets
            WHERE product_id = %s;
        """, (product_id,))
        row = cur.fetchone()
        if row:
            name, category = row
        else:
            raise Exception(f"Product details not found for product_id {product_id} in delivery {delivery_id}")

        pellet_ids = []
        for _ in range(quantity):
            cur.execute("""
                INSERT INTO product_pellet (
                    name, category, cost, weight, received,
                    sell_by, refrigerated, sent
                ) VALUES (%s, %s, %s, %s, %s, %s, FALSE, FALSE)
                RETURNING pellet_id;
            """, (
                name,
                category,
                get_pallet_cost(conn, product_id),
                get_product_weight(conn, product_id),
                current_date,
                current_date + timedelta(days=50)
            ))
            pellet_id = cur.fetchone()[0]
            pellet_ids.append(pellet_id)
        
        # Update inventory.
        cur.execute("""
            UPDATE inventory
            SET current_pellets = current_pellets + %s,
                to_be_received = GREATEST(to_be_received - %s, 0)
            WHERE inventory_id = 1;
        """, (quantity, quantity))
        # Log transaction using the computed cost.
        cur.execute("""
            INSERT INTO transactions (type, cost, date, date_time)
            VALUES ('supplier_delivery', %s, %s, %s);
        """, (computed_cost, current_date, current_date))
    conn.commit()
    
    return {
        "delivered_dict": {str(product_id): pellet_ids},
        "total_quantity": quantity,
        "total_cost": computed_cost,
        "total_weight": (weight if weight is not None else get_product_weight(conn, product_id)) * quantity
    }

def unload_supplier_deliveries(current_date):
    """
    Processes all pending supplier deliveries in single-product mode.
    """
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT transaction_id, product_id, quantity_received, cost, weight, date_time
            FROM supplier_delivery
            WHERE status = 'pending'
            ORDER BY date_time ASC;
        """)
        deliveries = cur.fetchall()
    
    for delivery in deliveries:
        try:
            summary = unload_supplier_delivery(conn, delivery, current_date)
            #print(f"Processed delivery {delivery[0]} on {current_date}. Summary: {summary}")
        except Exception as e:
            conn.rollback()
            #print(f"Error processing delivery {delivery[0]} on {current_date}: {e}")
            continue
