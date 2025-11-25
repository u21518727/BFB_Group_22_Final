from flask import Flask, render_template, send_file, send_from_directory, request, redirect, url_for, flash, abort, session
import sqlite3
from fpdf import FPDF
import io
from datetime import datetime

app = Flask(__name__, 
    template_folder='Templates',
    static_folder='static',
    static_url_path='/static')
app.secret_key = 'your-secret-key-here'  # Required for flash messages and sessions


@app.route('/styles.css')
def serve_root_styles():
    try:
        return send_from_directory('static', 'styles.css')
    except Exception:
        abort(404)


@app.route('/')
def home():
    # Connect to the provided database
    conn = sqlite3.connect('newdata.db')
    conn.row_factory = sqlite3.Row

    # Number of distinct products
    products_count = conn.execute('SELECT COUNT(*) FROM new_product').fetchone()[0]

    # Total items across inventory (sum of quantities)
    items_count = conn.execute('SELECT SUM(quantity) FROM update_inventory').fetchone()[0]
    if items_count is None:
        items_count = 0

    # There is no price column in this DB schema; leave total_value as None
    total_value = None

    # Build a product list with aggregated quantities (join new_product with update_inventory)
    products = conn.execute(
        '''SELECT np.product_id AS sku,
                  np.product_name AS product_name,
                  IFNULL(SUM(ui.quantity), 0) AS quantity
           FROM new_product np
           LEFT JOIN update_inventory ui ON np.product_id = ui.product_id
           GROUP BY np.product_id, np.product_name
           ORDER BY np.product_name'''
    ).fetchall()

    conn.close()
    return render_template('Home.html', products_count=products_count, items_count=items_count, total_value=total_value, products=products)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Connect to database
        conn = sqlite3.connect('newdata.db')
        conn.row_factory = sqlite3.Row
        
        # Check customer credentials
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM customer WHERE cust_email = ? AND cust_password = ?', (email, password))
        customer = cursor.fetchone()
        conn.close()
        
        if customer:
            # Successful login - store user info in session
            session['user_id'] = customer['customer_id']
            session['user_name'] = f"{customer['cust_name']} {customer['cust_surname']}"
            session['user_type'] = 'customer'
            return redirect(url_for('customer_dashboard'))
        else:
            # Failed login - show error and return to login page
            flash('Invalid email or password. Please try again.', 'error')
            return redirect(url_for('login'))
    
    # GET request - just render the login page
    return render_template('Customer_login.html')


@app.route('/customer_dashboard')
def customer_dashboard():
    # Protect this route - only accessible to logged-in customers
    if 'user_id' not in session or session.get('user_type') != 'customer':
        flash('Please log in to access your dashboard.', 'warning')
        return redirect(url_for('login'))
    
    customer_id = session['user_id']

    # Connect to the database
    conn = sqlite3.connect('newdata.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get this customer's orders, with location name
    cursor.execute("""
        SELECT co.order_id,
               co.grc_items,
               l.loacation_name
        FROM cust_order AS co
        JOIN location AS l
          ON co.location_id = l.location_id
        WHERE co.customer_id = ?
        ORDER BY co.order_id DESC
    """, (customer_id,))
    orders = cursor.fetchall()

    conn.close()

    # Pass orders to the template
    return render_template(
        'Customer.html',
        user_name=session.get('user_name'),
        orders=orders
    )



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        surname = request.form.get('surname')
        email = request.form.get('email')
        location = request.form.get('location')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm-password')
        
        # Basic validation
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('register'))
        
        # Connect to database
        conn = sqlite3.connect('newdata.db')
        cursor = conn.cursor()
        
        # Check if email already exists
        cursor.execute('SELECT customer_id FROM customer WHERE cust_email = ?', (email,))
        if cursor.fetchone():
            conn.close()
            flash('Email already registered. Please use a different email or log in.', 'error')
            return redirect(url_for('register'))
        
        # Insert new customer
        try:
            cursor.execute('''
                INSERT INTO customer (cust_name, cust_surname, cust_email, cust_location, cust_password)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, surname, email, location, password))
            
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            conn.rollback()
            flash('Error creating account. Please try again.', 'error')
            return redirect(url_for('register'))
        finally:
            conn.close()
    
    # GET request - render registration form
    return render_template('Customer_registration.html')


@app.route('/staff_register', methods=['GET', 'POST'])
def staff_register():
    if request.method == 'POST':
        # Get form data
        employee_id = request.form.get('employee-id')
        name = request.form.get('name')
        surname = request.form.get('surname')
        email = request.form.get('email')
        phone = request.form.get('phone')
        department = request.form.get('department')
        position = request.form.get('position')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm-password')
        
        # Basic validation
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('staff_register'))
        
        # Connect to database
        conn = sqlite3.connect('newdata.db')
        cursor = conn.cursor()
        
        # Check if employee ID or email already exists
        cursor.execute('SELECT staff_id FROM staff WHERE staff_id = ? OR staff_email = ?', (employee_id, email))
        if cursor.fetchone():
            conn.close()
            flash('Employee ID or email already registered.', 'error')
            return redirect(url_for('staff_register'))
        
        # Map department name to department_id
        dept_map = {
            'inventory': 1,
            'sales': 2,
            'customer-service': 3,
            'logistics': 4,
            'admin': 5
        }
        department_id = dept_map.get(department, 1)
        
        # Insert new staff member
        try:
            cursor.execute('''
                INSERT INTO staff (staff_id, staff_name, staff_surname, staff_email, phone_nmr, position, staff_password, department_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (employee_id, name, surname, email, phone, position, password, department_id))
            
            conn.commit()
            flash('Staff registration successful! Please log in.', 'success')
            return redirect(url_for('verify_staff'))
            
        except Exception as e:
            conn.rollback()
            flash('Error creating staff account. Please try again.', 'error')
            return redirect(url_for('staff_register'))
        finally:
            conn.close()
    
    # GET request - render staff registration form
    return render_template('Staff_registration.html')


@app.route('/submit_order', methods=['POST'])
def submit_order():
    """Handle customer order submission"""
    if 'user_id' not in session or session.get('user_type') != 'customer':
        flash('Please log in to submit an order.', 'warning')
        return redirect(url_for('login'))
    
    try:
        items = request.form.get('items')
        location = request.form.get('current-location')
        customer_id = session['user_id']
        
        if not items:
            flash('Please enter items for your order.', 'error')
            return redirect(url_for('customer_dashboard'))
        
        # Find location ID
        conn = sqlite3.connect('newdata.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT location_id FROM location WHERE loacation_name = ?', (location,))
        location_row = cursor.fetchone()
        
        if location_row:
            location_id = location_row[0]
        else:
            # Default to first location if not found
            location_id = 1
        
        # Insert order
        cursor.execute('''
            INSERT INTO cust_order (grc_items, customer_id, location_id)
            VALUES (?, ?, ?)
        ''', (items, customer_id, location_id))
        
        conn.commit()
        conn.close()
        
        flash('Order submitted successfully!', 'success')
        return redirect(url_for('customer_dashboard'))
        
    except Exception as e:
        print(f"Error submitting order: {str(e)}")
        flash('Error submitting order. Please try again.', 'error')
        return redirect(url_for('customer_dashboard'))


@app.route('/inventory')
def inventory():
    conn = sqlite3.connect('newdata.db')
    cursor = conn.cursor()
    
    # Get all products with their categories and quantities
    cursor.execute('''
        SELECT 
            np.product_id,
            np.product_name,
            c.category_name,
            IFNULL(SUM(ui.quantity), 0) as quantity
        FROM new_product np
        LEFT JOIN categories c ON np.category_id = c.category_id
        LEFT JOIN update_inventory ui ON np.product_id = ui.product_id
        GROUP BY np.product_id, np.product_name, c.category_name
        ORDER BY c.category_name, np.product_name
    ''')
    products = cursor.fetchall()
    conn.close()
    return render_template('inventory.html', products=products)




@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        # Get form data
        product_name = request.form.get('product-name')
        product_id = request.form.get('product-id')
        min_qty = request.form.get('min-quantity')
        max_qty = request.form.get('max-quantity')
        category = request.form.get('Categorie')
        
        # Connect to database
        conn = sqlite3.connect('newdata.db')
        cursor = conn.cursor()
        
        try:
            # Insert new product
            cursor.execute('''
                INSERT INTO new_product (product_id, product_name, min_qty, max_qty, category_id, staff_id)
                VALUES (?, ?, ?, ?, (SELECT category_id FROM categories WHERE category_name = ?), 1)
            ''', (product_id, product_name, min_qty, max_qty, category))
            
            conn.commit()
            flash('Product added successfully!', 'success')
            return redirect(url_for('inventory'))
            
        except Exception as e:
            conn.rollback()
            flash('Error adding product. Please try again.', 'error')
            return redirect(url_for('add_product'))
        finally:
            conn.close()
    
    # GET request - render form
    return render_template('inventory_products.html')


@app.route('/view_inventory')
def view_inventory():
    conn = sqlite3.connect('newdata.db')
    conn.row_factory = sqlite3.Row
    products = conn.execute(
        '''SELECT np.product_id AS sku,
                  np.product_name AS product_name,
                  IFNULL(SUM(ui.quantity), 0) AS quantity
           FROM new_product np
           LEFT JOIN update_inventory ui ON np.product_id = ui.product_id
           GROUP BY np.product_id, np.product_name
           ORDER BY np.product_name'''
    ).fetchall()
    conn.close()
    return render_template('inventory_products.html', products=products)


@app.route('/download_inventory_pdf')
def download_inventory_pdf():
    try:
        # Connect to database
        conn = sqlite3.connect('newdata.db')
        cursor = conn.cursor()
        
        # Get inventory data with categories
        cursor.execute('''
            SELECT 
                np.product_id,
                np.product_name,
                c.category_name,
                IFNULL(SUM(ui.quantity), 0) as quantity
            FROM new_product np
            LEFT JOIN categories c ON np.category_id = c.category_id
            LEFT JOIN update_inventory ui ON np.product_id = ui.product_id
            GROUP BY np.product_id, np.product_name, c.category_name
            ORDER BY c.category_name, np.product_name
        ''')
        products = cursor.fetchall()
        conn.close()

        # Create PDF
        pdf = FPDF()
        pdf.add_page('L')  # Landscape orientation for better table fit
        
        # Set up title
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'GrocerEase Inventory Report', 0, 1, 'C')
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 10, f'Generated on {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 1, 'C')
        pdf.ln(10)
        
        # Table header with more width in landscape mode
        pdf.set_font('Arial', 'B', 12)
        col_widths = [30, 100, 80, 40]  # Adjusted column widths
        headers = ['ID', 'Product Name', 'Category', 'Quantity']
        
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 10, header, 1)
        pdf.ln()
        
        # Table content
        pdf.set_font('Arial', '', 12)
        for product in products:
            # Add a row of data
            pdf.cell(col_widths[0], 10, str(product[0]), 1)
            pdf.cell(col_widths[1], 10, str(product[1]), 1)
            pdf.cell(col_widths[2], 10, str(product[2]), 1)
            pdf.cell(col_widths[3], 10, str(product[3]), 1)
            pdf.ln()

        # Create PDF in memory buffer instead of file
        pdf_buffer = io.BytesIO()
        pdf_bytes = pdf.output(dest='S').encode('latin-1')  
        pdf_buffer.write(pdf_bytes)
        pdf_buffer.seek(0)
        
        # Send the PDF directly from memory
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'inventory_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        )
                
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        return "Error generating PDF", 500

@app.route('/staff')
def staff():
    return render_template('Staff.html')

@app.route('/update_inventory', methods=['POST'])
def update_inventory():
    try:
        # Get values from the form
        product_id = int(request.form.get('product_id'))
        category_id = int(request.form.get('category'))
        quantity = int(request.form.get('quantity'))
        location_id = int(request.form.get('location'))

        # Connect to database
        conn = sqlite3.connect('newdata.db')
        cursor = conn.cursor()

        # Insert one inventory record (staff_id hard-coded as 1)
        cursor.execute(
            '''
            INSERT INTO update_inventory (quantity, product_id, location_id, staff_id, category_id)
            VALUES (?, ?, ?, ?, ?)
            ''',
            (quantity, product_id, location_id, 1, category_id)
        )

        conn.commit()
        conn.close()

        return redirect(url_for('inventory'))

    except Exception as e:
        print(f"Error updating inventory: {str(e)}")
        return "Error updating inventory", 500


@app.route('/verify_staff', methods=['GET', 'POST'])
def verify_staff():
    if request.method == 'POST':
        staff_id = request.form.get('staff-id')
        password = request.form.get('password')
        
        # Connect to database
        conn = sqlite3.connect('newdata.db')
        conn.row_factory = sqlite3.Row
        
        # Check staff credentials
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM staff WHERE staff_id = ? AND staff_password = ?', (staff_id, password))
        staff = cursor.fetchone()
        conn.close()
        
        if staff:
            # Successful login - store user info in session
            session['user_id'] = staff['staff_id']
            session['user_name'] = f"{staff['staff_name']} {staff['staff_surname']}"
            session['user_type'] = 'staff'
            return redirect(url_for('staff'))
        else:
            # Failed login - show error and return to login page
            flash('Invalid staff ID or password. Please try again.', 'error')
            return redirect(url_for('verify_staff'))
    
    # GET request - just render the verification page
    return render_template('Verification.html')

@app.route('/logout')
def logout():
    # Clear session and redirect to home
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)