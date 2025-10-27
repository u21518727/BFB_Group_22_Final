# BFB Group Project Final

A simple web-based STORE NAVIGATION FOR ENHANCED RETAIL SUPPLY
CHAIN EFFICIENCY system built with HTML, CSS, and SQL.

## Features

- **Home**: Overview of our system GrocerEase and indicate to sign in/up as customer or staff.
- **Customer Login**:This is a placeholder page to create an account to receive personalised recommendations and faster checkout.
- **Customer Registration**:This is a placeholder page for customer login. In a real application, this would include authentication mechanisms.
- **Customer Portal**:From here you can submit grocery items, view products and check order status.
- **Staff Verification**:This is a placeholder page for staff verification. In a real application, this would include authentication mechanisms.
- **Staff Dashboard**:Quick tools to manage inventory, process orders and help customers efficiently. This form is a simple placeholder for updating inventory items.
- **Inventory Overview**:Live counts and quick actions restock alerts highlight low stock automatically.
- **Add new Inventory**: Use the form to add a new product and the details of the product to the inventory.
- **Other**:-Contact-Privacy policy-Terms of service

## Database Setup

### Using SQLite Command Line

1. Open command prompt/terminal in the project directory
2. Run the SQL commands:
   ```bash
   sqlite3 inventory.db < inventory.sql
   ```

## Database Schema

### Entity Relationship Diagram (ERD)

```mermaid

erDiagram
    customer {
        INTEGER customer_id PK
        TEXT    cust_name
        TEXT    cust_surname
        TEXT    cust_email UK
        TEXT    cust_location       
        TEXT    cust_password
        DATETIME created_at
        DATETIME updated_at
    }

    staff {
        INTEGER staff_id PK
        TEXT    staff_name
        TEXT    staff_surname
        TEXT    staff_email UK
        TEXT    phone_nmr UK
        TEXT    position
        TEXT    staff_password
        INTEGER department_id FK
        DATETIME created_at
        DATETIME updated_at
    }

    categories {
        INTEGER category_id PK
        TEXT    category_name UK
        DATETIME created_at
    }

    new_product {
        INTEGER product_id PK     
        TEXT    product_name
        INTEGER min_qty
        INTEGER max_qty
        INTEGER category_id FK
        INTEGER staff_id FK
        DATETIME created_at
        DATETIME updated_at
    }

    location {
        INTEGER location_id PK
        TEXT    location_name       
        DATETIME created_at
        DATETIME updated_at
    }

    update_inventory {
        INTEGER update_id PK         
        INTEGER quantity
        INTEGER product_id FK
        INTEGER location_id FK
        INTEGER staff_id FK
        INTEGER category_id FK
        DATETIME created_at
        DATETIME updated_at
    }

    cust_order {
        INTEGER order_id PK
        TEXT   grc_items
        INTEGER customer_id FK
        INTEGER location_id FK    
        DATETIME submitted_at
        DATETIME updated_at
    }

    department {
        INTEGER department_id PK
        TEXT    department_name
        DATETIME created_at
        DATETIME updated_at
    }

    customer ||--o{ cust_order : "places"
    cust_order ||--|| location : "at"
    
    update_inventory ||--|| location : "at"

    categories ||--|| update_inventory : "categorizes"
    categories ||--|| new_product : "categorizes"

    staff ||--|| department : "at which"
    staff  ||--o{ new_product : "adds"
    staff ||--o{ update_inventory : "updates"
    
    update_inventory ||--o{ new_product : "add to"



```

The database includes the following tables:

### Tables

1. **product_categories**: Product categories (Electronics, Clothing, Books, etc.)
2. **vendors**: Registered vendors and their business information
3. **products**: Product inventory with SKU, name, quantity, price, etc.
4. **stock_updates**: History of all stock level changes

### Views

1. **low_stock_products**: View of products with low stock alerts
2. **inventory_summary**: Summary statistics for the dashboard

## Sample Data

The database includes sample data for testing:

- **9 Categories**: Electronics, Clothing, Books, Food & Beverages, Tools & Hardware, Furniture, Beauty & Health, Sports & Outdoors, Other
- **1 Vendor**: John Doe (TechStore Solutions)
- **10 Products**: Various items across different categories with realistic pricing and quantities
- **8 Stock Updates**: Sample transaction history

## File Structure

```
├── index.html              # Main dashboard
├── login.html              # Vendor login page
├── register.html           # Vendor registration page
├── add-product.html        # Add new products
├── view-inventory.html     # View all inventory
├── update-stock.html       # Update stock levels
├── inventory.sql           # Database schema and sample data
├── inventory.db            # SQLite database (created after running setup)
└── readme.md              # This file
```

## Usage

1. Initialize the database using the SQLite command line method above
2. Open `index.html` in your web browser
3. Navigate through the different pages to manage your inventory

## Technologies Used

- **HTML5**: Structure and forms
- **Bootstrap 5.3.8**: UI framework and styling
- **Bootstrap Icons**: Icon set
- **SQLite**: Database for data persistence

## Browser Compatibility

The application works with all modern browsers that support HTML5 and CSS3, including:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

Note: This is a static HTML application. For production use, you would need to add backend functionality for database connectivity and form processing.
