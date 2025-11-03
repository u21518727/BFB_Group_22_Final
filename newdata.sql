--
-- File generated with SQLiteStudio v3.4.17 on Mon Nov 3 19:34:25 2025
--
-- Text encoding used: System
--
PRAGMA foreign_keys = on;
BEGIN TRANSACTION;

-- Table: categories
DROP TABLE IF EXISTS categories;
CREATE TABLE categories (category_id INTEGER PRIMARY KEY, category_name TEXT UNIQUE);
INSERT INTO categories (category_id, category_name) VALUES (1, 'Meat');
INSERT INTO categories (category_id, category_name) VALUES (2, 'Poultry');
INSERT INTO categories (category_id, category_name) VALUES (3, 'Fish');
INSERT INTO categories (category_id, category_name) VALUES (4, 'Produce');
INSERT INTO categories (category_id, category_name) VALUES (5, 'Dairy');
INSERT INTO categories (category_id, category_name) VALUES (6, 'Bakery');
INSERT INTO categories (category_id, category_name) VALUES (7, 'Starch');
INSERT INTO categories (category_id, category_name) VALUES (8, 'Beverages');
INSERT INTO categories (category_id, category_name) VALUES (9, 'Cleaning Supplies');
INSERT INTO categories (category_id, category_name) VALUES (10, 'Electronics');
INSERT INTO categories (category_id, category_name) VALUES (11, 'Other');

-- Table: cust_order
DROP TABLE IF EXISTS cust_order;
CREATE TABLE cust_order (order_id INTEGER PRIMARY KEY, grc_items TEXT, customer_id INTEGER REFERENCES customer (customer_id), location_id INTEGER REFERENCES location (location_id));

-- Table: customer
DROP TABLE IF EXISTS customer;
CREATE TABLE customer (customer_id INTEGER PRIMARY KEY, cust_name TEXT, cust_surname TEXT, cust_email TEXT UNIQUE, cust_location TEXT, cust_password TEXT);

-- Table: department
DROP TABLE IF EXISTS department;
CREATE TABLE department (department_id INTEGER PRIMARY KEY, department_name TEXT);
INSERT INTO department (department_id, department_name) VALUES (1, 'Inventory Management');
INSERT INTO department (department_id, department_name) VALUES (2, 'Sales');
INSERT INTO department (department_id, department_name) VALUES (3, 'Customer Service');
INSERT INTO department (department_id, department_name) VALUES (4, 'Logistics');
INSERT INTO department (department_id, department_name) VALUES (5, 'Administration');

-- Table: location
DROP TABLE IF EXISTS location;
CREATE TABLE location (location_id INTEGER PRIMARY KEY, loacation_name TEXT);

-- Table: new_product
DROP TABLE IF EXISTS new_product;
CREATE TABLE new_product (product_id INTEGER PRIMARY KEY, product_name TEXT, min_qty INTEGER, max_qty INTEGER, category_id INTEGER REFERENCES categories (category_id), staff_id INTEGER REFERENCES staff (staff_id));

-- Table: staff
DROP TABLE IF EXISTS staff;
CREATE TABLE staff (staff_id INTEGER PRIMARY KEY, staff_name TEXT, staff_surname TEXT, staff_email TEXT UNIQUE, phone_nmr TEXT UNIQUE, position TEXT, staff_password TEXT, department_id INTEGER REFERENCES department (department_id));

-- Table: update_inventory
DROP TABLE IF EXISTS update_inventory;
CREATE TABLE update_inventory (update_id INTEGER PRIMARY KEY, quantity INTEGER, product_id TEXT REFERENCES new_product (product_id), location_id INTEGER REFERENCES location (location_id), staff_id INTEGER REFERENCES staff (staff_id), category_id INTEGER REFERENCES categories (category_id));

COMMIT TRANSACTION;
PRAGMA foreign_keys = off;
