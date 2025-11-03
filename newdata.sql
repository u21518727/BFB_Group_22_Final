-- SQLite Database Schema (Fixed)
PRAGMA foreign_keys = ON;
BEGIN TRANSACTION;

-- Drop existing tables (if any)
DROP TABLE IF EXISTS update_inventory;
DROP TABLE IF EXISTS cust_order;
DROP TABLE IF EXISTS new_product;
DROP TABLE IF EXISTS staff;
DROP TABLE IF EXISTS customer;
DROP TABLE IF EXISTS location;
DROP TABLE IF EXISTS department;
DROP TABLE IF EXISTS categories;

-- Table: department
CREATE TABLE department (
    department_id INTEGER PRIMARY KEY,
    department_name TEXT
);

-- Table: staff
CREATE TABLE staff (
    staff_id INTEGER PRIMARY KEY,
    staff_name TEXT,
    staff_surname TEXT,
    staff_email TEXT UNIQUE,
    phone_nmr TEXT UNIQUE,
    position TEXT,
    staff_password TEXT,
    department_id INTEGER REFERENCES department (department_id)
);

-- Table: categories
CREATE TABLE categories (
    category_id INTEGER PRIMARY KEY,
    category_name TEXT UNIQUE
);

-- Table: location
CREATE TABLE location (
    location_id INTEGER PRIMARY KEY,
    loacation_name TEXT
);

-- Table: customer
CREATE TABLE customer (
    customer_id INTEGER PRIMARY KEY,
    cust_name TEXT,
    cust_surname TEXT,
    cust_email TEXT UNIQUE,
    cust_location TEXT,
    cust_password TEXT
);

-- Table: new_product
CREATE TABLE new_product (
    product_id INTEGER PRIMARY KEY,
    product_name TEXT,
    min_qty INTEGER,
    max_qty INTEGER,
    category_id INTEGER REFERENCES categories (category_id),
    staff_id INTEGER REFERENCES staff (staff_id)
);

-- Table: update_inventory
CREATE TABLE update_inventory (
    update_id INTEGER PRIMARY KEY,
    quantity INTEGER,
    product_id INTEGER REFERENCES new_product (product_id),
    location_id INTEGER REFERENCES location (location_id),
    staff_id INTEGER REFERENCES staff (staff_id),
    category_id INTEGER REFERENCES categories (category_id)
);

-- Table: cust_order
CREATE TABLE cust_order (
    order_id INTEGER PRIMARY KEY,
    grc_items TEXT,
    customer_id INTEGER REFERENCES customer (customer_id),
    location_id INTEGER REFERENCES location (location_id)
);

-- Insert sample department
INSERT INTO department VALUES
(1, 'Inventory Management'),
(2, 'Sales'),
(3, 'Customer Service'),
(4, 'Logistics'),
(5, 'Administration');

-- Insert sample staff
INSERT INTO staff VALUES
(1, 'Louwhann', 'Crous', 'louwhann.crous@company.co.za', '0712345678', 'Inventory Clerk', 'invpass1', 1),
(2, 'Pieter', 'van Wyk', 'pieter.vanwyk@company.co.za', '0723456789', 'Sales Representative', 'sales22', 2),
(3, 'Sebastian', 'du Toit', 'sebastian.dutoit@company.co.za', '0734567890', 'Customer Service Agent', 'cust99', 3),
(4, 'Johan', 'Steyn', 'johan.steyn@company.co.za', '0745678901', 'Logistics Coordinator', 'logis77', 4),
(5, 'Naledi', 'Mokoena', 'naledi.mokoena@company.co.za', '0756789012', 'Admin Officer', 'admin11', 5);

-- Insert sample categories
INSERT INTO categories VALUES
(1, 'Meat'),
(2, 'Poultry'),
(3, 'Fish'),
(4, 'Produce'),
(5, 'Dairy'),
(6, 'Bakery'),
(7, 'Starch'),
(8, 'Beverages'),
(9, 'Cleaning Supplies'),
(10, 'Electronics'),
(11, 'Other');

-- Insert sample locations
INSERT INTO location VALUES
(1, 'Centurion'),
(2, 'Hatfield'),
(3, 'Kempton Park'),
(4, 'Midrand'),
(5, 'Sandton');

-- Insert customers
INSERT INTO customer VALUES
(1, 'Wandre', 'Nel', 'wandre.nel@example.com', 'Centurion', 'pass123'),
(2, 'Thabo', 'Nkosi', 'thabo.nkosi@example.com', 'Hatfield', 'secure456'),
(3, 'Megan', 'Botha', 'megan.botha@example.com', 'Kempton Park', 'megan789'),
(4, 'Christiaan', 'Conradie', 'christiaan.conradie@example.com', 'Midrand', 'chris321');

-- Insert products
INSERT INTO new_product VALUES
(1, 'Beef Mince 500g', 10, 100, 1, 1),
(2, 'Whole Chicken 1kg', 8, 80, 2, 1),
(3, 'Hake Fillet 500g', 5, 50, 3, 1),
(4, 'Fresh Apples 1kg', 15, 150, 4, 1),
(5, 'Full Cream Milk 2L', 20, 200, 5, 1),
(6, 'Brown Bread', 25, 250, 6, 1),
(7, 'White Rice 2kg', 10, 120, 7, 1),
(8, 'Coca-Cola 2L', 30, 300, 8, 1),
(9, 'Dishwashing Liquid 750ml', 10, 100, 9, 1),
(10, 'Laptop Charger', 5, 50, 10, 1);

-- Insert inventory
INSERT INTO update_inventory VALUES
(1, 50, 1, 1, 1, 1),
(2, 30, 2, 2, 1, 2),
(3, 20, 3, 3, 1, 3),
(4, 100, 4, 4, 1, 4),
(5, 80, 5, 5, 1, 5),
(6, 200, 6, 1, 1, 6),
(7, 150, 7, 2, 1, 7),
(8, 300, 8, 3, 1, 8),
(9, 90, 9, 4, 1, 9),
(10, 40, 10, 5, 1, 10);

-- Insert orders
INSERT INTO cust_order VALUES
(1, 'Beef Mince, Chicken Fillet, Milk', 1, 1),
(2, 'Brown Bread, Butter, Apples', 2, 2),
(3, 'Coke, Chips, Cheese', 3, 3),
(4, 'Laptop Charger, Bread Rolls', 4, 4);

COMMIT TRANSACTION;
