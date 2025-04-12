-- STORE TABLE: Represents each store receiving deliveries
CREATE TABLE store (
    store_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    address TEXT NOT NULL,
    distance_km FLOAT, -- Distance from the warehouse
    expected_time INTERVAL, -- Expected travel time
    open_time TIME, -- Store opening time
    close_time TIME -- Store closing time
);

CREATE TABLE pending_orders (
    id SERIAL PRIMARY KEY,
    store_id TEXT,
    products JSON,
    date_time TIMESTAMP
);

-- PRODUCT PELLETS SUMMARY: Aggregated product inventory
CREATE TABLE product_pellets (
    product_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    quantity INT, -- Number of units of product available
    pallet_cost FLOAT -- Cost per pallet for use in delivery pricing
);

-- PRODUCT PELLET TABLE: Tracks individual pallets in warehouse
CREATE TABLE product_pellet (
    pellet_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    cost INT,
    weight FLOAT, -- Weight of the pallet
    received DATE, -- Date pallet was received
    sell_by DATE, -- Sell-by date for perishables
    refrigerated BOOLEAN, -- Whether the pallet needs refrigeration
    sent BOOLEAN -- Whether the pallet has already been sent
);

-- INVENTORY TABLE: Overview of warehouse inventory status
CREATE TABLE inventory (
    inventory_id SERIAL,
    capacity_pellets INT, -- Max number of pallets warehouse can hold
    current_pellets INT, -- Currently stored pallets
    to_be_sent INT, -- Pallets scheduled to be sent
    to_be_received INT -- Pallets expected from suppliers
);

-- EMPLOYEE TABLE: Staff and drivers
CREATE TABLE employee (
    employee_id SERIAL PRIMARY KEY,
    name TEXT,
    phone_num TEXT,
    job_role TEXT, -- e.g., 'driver'
    salary FLOAT,
    account_num TEXT,
    hours_week INT,
    next_payment DATE
);

-- TRUCK TABLE: Tracks delivery trucks
CREATE TABLE truck (
    truck_id SERIAL PRIMARY KEY,
    employee_id INT REFERENCES employee(employee_id),
    plate_number TEXT,
    refrigerated BOOLEAN, -- Whether the truck has refrigeration
    capacity FLOAT, -- Max capacity in weight
    km_driven FLOAT, -- Total kilometers driven
    operational_status TEXT, -- e.g., 'available', 'maintenance'
    fuel_capacity FLOAT, -- Liters of fuel tank
    last_maintanance DATE
);

-- INVENTORY DELIVERY TABLE: Outbound delivery records to stores
CREATE TABLE inventory_delivery (
    transaction_id SERIAL PRIMARY KEY,
    store_sent TEXT REFERENCES store(store_id),
    products_delivered TEXT,
    quantities_delivered TEXT,
    cost FLOAT,
    truck_sent INT REFERENCES truck(truck_id),
    driver_sent INT REFERENCES employee(employee_id),
    time_sent TIMESTAMP,
    time_returned TIMESTAMP,
    quantity INT,
    status TEXT,
    date_time TIMESTAMP
);

-- TRUCK LOG: Logs each truck’s route
CREATE TABLE truck_log (
    log_id SERIAL PRIMARY KEY,
    delivery_id INT REFERENCES inventory_delivery(transaction_id),
    driver_id INT REFERENCES employee(employee_id),
    time_sent TIMESTAMP,
    time_returned TIMESTAMP,
    expected_time INTERVAL,
    status TEXT, -- e.g., 'on_time', 'delayed'
    distance_km FLOAT,
    km_driven_delivery FLOAT,
    extra_km FLOAT, -- Deviation from optimal route
    delivery_delay INTERVAL, -- Delay duration if any
    date_time TIMESTAMP
);

-- TRANSACTIONS TABLE: Logs all financial transactions
CREATE TABLE transactions (
    transaction_id SERIAL PRIMARY KEY,
    type TEXT, -- e.g., 'delivery', 'supplier_delivery', 'fuel', 'payroll'
    cost FLOAT,
    date DATE,
    date_time TIMESTAMP
);
CREATE INDEX idx_transactions_date ON transactions(date);
CREATE INDEX idx_transactions_type ON transactions(type);

-- FUEL LOG: Fuel purchases per truck
CREATE TABLE fuel_log (
    transaction_id INT PRIMARY KEY REFERENCES transactions(transaction_id),
    truck_id INT REFERENCES truck(truck_id),
    employee_id INT REFERENCES employee(employee_id),
    cost FLOAT,
    liters FLOAT,
    cost_per_liter FLOAT,
    expected_cost FLOAT,
    date_time TIMESTAMP
);

-- PAYROLL LOG: Salary transactions
CREATE TABLE payroll_log (
    transaction_id INTEGER PRIMARY KEY REFERENCES transactions(transaction_id),
    employee_id INT REFERENCES employee(employee_id),
    payment FLOAT,
    account_num TEXT,
    last_payment DATE,
    next_payment DATE,
    date_time TIMESTAMP
);

-- SUPPLIER TABLE: Product suppliers and delivery expectations
CREATE TABLE supplier (
    supplier_id TEXT PRIMARY KEY,
    expected_delivery_time INTERVAL,
    product_id INT REFERENCES product_pellets(product_id),
    product_category TEXT
);

-- SUPPLIER DELIVERY TABLE: Incoming deliveries from suppliers
CREATE TABLE supplier_delivery (
    transaction_id SERIAL PRIMARY KEY,
    supplier_id TEXT REFERENCES supplier(supplier_id),
    expected_delivery_time INTERVAL,
    order_sent TIMESTAMP,
    order_received TIMESTAMP,
    status TEXT, -- e.g., 'pending', 'received'
    cost FLOAT, -- Cost of received delivery
    product_id INT REFERENCES product_pellets(product_id),
    pellet_id INT REFERENCES product_pellet(pellet_id),
    quantity_received INT,
    weight FLOAT,
    date_time TIMESTAMP
);

-- OVERSPENDING TABLE: Logs any financial anomalies
CREATE TABLE overspending_log (
    id SERIAL PRIMARY KEY,
    transaction_id INT REFERENCES transactions(transaction_id),
    type TEXT, -- 'fuel', 'delivery', 'payroll'
    expected_cost FLOAT,
    actual_cost FLOAT,
    deviation FLOAT,
    reason TEXT,
    flagged_by TEXT DEFAULT 'system',
    date_time TIMESTAMP DEFAULT NOW(),
    employee_id INT REFERENCES employee(employee_id)
);

-- UNDERPERFORMANCE TABLE: Logs any underperformance by employees
CREATE TABLE underperformance_log (
    id SERIAL PRIMARY KEY,
    delivery_id INT REFERENCES inventory_delivery(transaction_id),
    entity_type TEXT, -- 'truck'
    entity_id INT REFERENCES employee(employee_id),
    event_type TEXT, -- 'delivery_delay', 'route_deviation'
    expected_duration INTERVAL,
    actual_duration INTERVAL,
    deviation INTERVAL,
    reason TEXT,
    flagged_by TEXT DEFAULT 'system',
    date_time TIMESTAMP DEFAULT NOW()
);

CREATE TABLE system_config (
    key TEXT PRIMARY KEY,
    value TEXT
);
INSERT INTO system_config (key, value) VALUES ('current_gas_price', '3.00');
ALTER TABLE supplier_delivery DROP CONSTRAINT supplier_delivery_supplier_id_fkey;
ALTER TABLE supplier DROP CONSTRAINT supplier_pkey;

-- Incase of unforseen errors
-- TRUNCATE TABLE transactions RESTART IDENTITY CASCADE; --- remove all data from transactions table
-- SELECT setval(pg_get_serial_sequence('transactions', 'transaction_id'), (SELECT MAX(transaction_id) FROM transactions)); --- reset sequence for transaction_id
-- UPDATE employee
-- SET next_payment = '2025-04-07'
-- WHERE next_payment IS NULL;
-- use the above to seed initial payment date
