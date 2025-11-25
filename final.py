from flask import Flask, render_template, send_file, send_from_directory, request, redirect, url_for, flash, abort, session
import sqlite3
from fpdf import FPDF
import io
from datetime import datetime
import os
import traceback

app = Flask(__name__, 
    template_folder='Templates',
    static_folder='static',
    static_url_path='/static')
app.secret_key = 'your-secret-key-here'

base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, 'newdata.db')
schema_path = os.path.join(base_dir, 'newdata.sql')
if not os.path.exists(db_path):
    if os.path.exists(schema_path):
        try:
            conn = sqlite3.connect(db_path)
            with open(schema_path, 'r', encoding='utf-8') as f:
                conn.executescript(f.read())
            conn.close()
            print(f"Created database '{db_path}' from schema '{schema_path}'")
        except Exception as e:
            print(f"Error creating database from schema: {e}")
    else:
        print(f"Warning: schema file '{schema_path}' not found. '{db_path}' will be created empty on first use.")

try:
    conn_m = sqlite3.connect(db_path)
    cur_m = conn_m.cursor()
    cur_m.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='backorder'")
    if cur_m.fetchone():
        cols = [r[1] for r in cur_m.execute("PRAGMA table_info(backorder)").fetchall()]
        if 'location_id' not in cols:
            try:
                cur_m.execute("ALTER TABLE backorder ADD COLUMN location_id INTEGER REFERENCES location(location_id)")
                conn_m.commit()
                print('Migrated: added backorder.location_id')
            except Exception as me:
                print(f'Could not add backorder.location_id: {me}')
    conn_m.close()
except Exception:
    pass


@app.route('/styles.css')
def serve_root_styles():
    try:
        return send_from_directory('static', 'styles.css')
    except Exception:
        abort(404)


@app.route('/')
def home():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    products_count = conn.execute('SELECT COUNT(*) FROM new_product').fetchone()[0]

    items_count = conn.execute('SELECT SUM(quantity) FROM update_inventory').fetchone()[0]
    if items_count is None:
        items_count = 0

    total_value = None

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
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM customer WHERE cust_email = ? AND cust_password = ?', (email, password))
        customer = cursor.fetchone()
        conn.close()
        
        if customer:
            session['user_id'] = customer['customer_id']
            session['user_name'] = f"{customer['cust_name']} {customer['cust_surname']}"
            session['user_type'] = 'customer'
            return redirect(url_for('customer_dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'error')
            return redirect(url_for('login'))
    
    return render_template('Customer_login.html')


@app.route('/customer_dashboard')
def customer_dashboard():
    if 'user_id' not in session or session.get('user_type') != 'customer':
        flash('Please log in to access your dashboard.', 'warning')
        return redirect(url_for('login'))
    
    customer_id = session['user_id']

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""SELECT co.order_id,
               co.grc_items,
               l.location_name
        FROM cust_order AS co
        LEFT JOIN location AS l
          ON co.location_id = l.location_id
        WHERE co.customer_id = ?
        ORDER BY co.order_id DESC
    """, (customer_id,))
    orders = cursor.fetchall()

    products = cursor.execute(
        'SELECT product_id, product_name FROM new_product ORDER BY product_name'
    ).fetchall()

    locations = cursor.execute('SELECT location_id, location_name FROM location ORDER BY location_name').fetchall()

    conn.close()

    return render_template(
        'Customer.html',
        user_name=session.get('user_name'),
        orders=orders,
        products=products,
        locations=locations
    )



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        surname = request.form.get('surname')
        email = request.form.get('email')
        location = request.form.get('location')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm-password')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('register'))
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT customer_id FROM customer WHERE cust_email = ?', (email,))
        if cursor.fetchone():
            conn.close()
            flash('Email already registered. Please use a different email or log in.', 'error')
            return redirect(url_for('register'))
        
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
    
    return render_template('Customer_registration.html')


@app.route('/staff_register', methods=['GET', 'POST'])
def staff_register():
    if request.method == 'POST':
        employee_id = request.form.get('employee-id')
        name = request.form.get('name')
        surname = request.form.get('surname')
        email = request.form.get('email')
        phone = request.form.get('phone')
        department = request.form.get('department')
        position = request.form.get('position')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm-password')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('staff_register'))
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT staff_id FROM staff WHERE staff_id = ? OR staff_email = ?', (employee_id, email))
        if cursor.fetchone():
            conn.close()
            flash('Employee ID or email already registered.', 'error')
            return redirect(url_for('staff_register'))
        
        dept_map = {
            'inventory': 1,
            'sales': 2,
            'customer-service': 3,
            'logistics': 4,
            'admin': 5
        }
        department_id = dept_map.get(department, 1)
        
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
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('SELECT MAX(staff_id) FROM staff')
    result = cursor.fetchone()
    next_staff_id = 1 if result[0] is None else result[0] + 1
    
    conn.close()
    
    return render_template('Staff_registration.html', next_staff_id=next_staff_id)


@app.route('/submit_order', methods=['POST'])
def submit_order():
    """Handle customer order submission"""
    print(f"DEBUG: /submit_order called")
    print(f"DEBUG: POST data: {request.form}")
    print(f"DEBUG: Session user_id: {session.get('user_id')}")
    
    if 'user_id' not in session or session.get('user_type') != 'customer':
        flash('Please log in to submit an order.', 'warning')
        return redirect(url_for('login'))
    
    try:
        product_ids = request.form.getlist('product_ids')
        print(f"DEBUG: product_ids from form: {product_ids}")
        customer_id = session['user_id']

        if not product_ids:
            print(f"DEBUG: No product_ids selected, re-rendering dashboard with error")
            flash('Please select at least one product for your order.', 'error')
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT co.order_id,
                       co.grc_items,
                       l.location_name
                FROM cust_order AS co
                LEFT JOIN location AS l
                  ON co.location_id = l.location_id
                WHERE co.customer_id = ?
                ORDER BY co.order_id DESC
            """, (customer_id,))
            orders = cursor.fetchall()
            products = cursor.execute(
                'SELECT product_id, product_name FROM new_product ORDER BY product_name'
            ).fetchall()
            conn.close()
            return render_template('Customer.html', user_name=session.get('user_name'), orders=orders, products=products)

        try:
            product_quantities = {}
            for pid in product_ids:
                pid_int = int(pid)
                qty_str = request.form.get(f'qty_{pid}', '1')
                qty = int(qty_str)
                if qty < 1:
                    flash(f'Invalid quantity for product {pid}. Minimum is 1.', 'error')
                    conn = sqlite3.connect(db_path)
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT co.order_id,
                               co.grc_items,
                               l.location_name
                        FROM cust_order AS co
                        LEFT JOIN location AS l
                          ON co.location_id = l.location_id
                        WHERE co.customer_id = ?
                        ORDER BY co.order_id DESC
                    """, (customer_id,))
                    orders = cursor.fetchall()
                    products = cursor.execute(
                        'SELECT product_id, product_name FROM new_product ORDER BY product_name'
                    ).fetchall()
                    conn.close()
                    return render_template('Customer.html', user_name=session.get('user_name'), orders=orders, products=products)
                product_quantities[pid_int] = qty
            product_ids_int = list(product_quantities.keys())
        except ValueError:
            flash('Invalid product selection or quantity.', 'error')
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT co.order_id,
                       co.grc_items,
                       l.location_name
                FROM cust_order AS co
                LEFT JOIN location AS l
                  ON co.location_id = l.location_id
                WHERE co.customer_id = ?
                ORDER BY co.order_id DESC
            """, (customer_id,))
            orders = cursor.fetchall()
            products = cursor.execute(
                'SELECT product_id, product_name FROM new_product ORDER BY product_name'
            ).fetchall()
            conn.close()
            return render_template('Customer.html', user_name=session.get('user_name'), orders=orders, products=products)

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        placeholders = ','.join('?' for _ in product_ids_int)
        prod_rows = cursor.execute(f'SELECT product_id, product_name FROM new_product WHERE product_id IN ({placeholders})', tuple(product_ids_int)).fetchall()
        
        items_with_qty = []
        for r in prod_rows:
            pid = r['product_id']
            qty = product_quantities[pid]
            items_with_qty.append(f"{qty}x {r['product_name']}")
        grc_items = ', '.join(items_with_qty)

        desired_location = request.form.get('current-location')
        try:
            desired_location_id = int(desired_location) if desired_location else 1
        except Exception:
            desired_location_id = 1

        sql = f"""
            SELECT l.location_id, l.location_name, ui.product_id, ui.quantity
            FROM location l
            JOIN update_inventory ui ON l.location_id = ui.location_id
            WHERE ui.product_id IN ({placeholders})
            ORDER BY l.location_id, ui.product_id
        """
        inv_rows = cursor.execute(sql, tuple(product_ids_int)).fetchall()
        location_inventory = {}
        for row in inv_rows:
            loc_id = row['location_id']
            prod_id = row['product_id']
            qty = row['quantity']
            if loc_id not in location_inventory:
                location_inventory[loc_id] = {}
            location_inventory[loc_id][prod_id] = qty

        available_locations = []
        for loc_id, inv_map in location_inventory.items():
            if all(inv_map.get(pid, 0) >= product_quantities[pid] for pid in product_ids_int):
                loc_row = cursor.execute('SELECT location_name FROM location WHERE location_id = ?', (loc_id,)).fetchone()
                available_locations.append((loc_id, loc_row['location_name']))

        location_id = desired_location_id

        cursor.execute('''
            INSERT INTO cust_order (grc_items, customer_id, location_id)
            VALUES (?, ?, ?)
        ''', (grc_items, customer_id, location_id))
        
        order_id = cursor.lastrowid
        print(f"DEBUG: Inserted order {order_id} at location {location_id}")
        
        for pid, qty in product_quantities.items():
            print(f"DEBUG: Processing product {pid}, requested qty {qty} at location {location_id}")

            inv_row = cursor.execute('''
                SELECT quantity FROM update_inventory
                WHERE product_id = ? AND location_id = ?
            ''', (pid, location_id)).fetchone()

            if inv_row:
                current_qty = inv_row[0]
                deduct = min(qty, current_qty)
                new_qty = current_qty - deduct
                cursor.execute('''
                    UPDATE update_inventory
                    SET quantity = ?
                    WHERE product_id = ? AND location_id = ?
                ''', (new_qty, pid, location_id))
                print(f"DEBUG: Deducted {deduct} from product {pid} at location {location_id} (was {current_qty}, now {new_qty})")

                if qty > current_qty:
                    shortage = qty - current_qty
                    cursor.execute('''
                        INSERT INTO backorder (order_id, product_id, requested_qty, available_qty, shortage, status, location_id)
                        VALUES (?, ?, ?, ?, ?, 'pending', ?)
                    ''', (order_id, pid, qty, current_qty, shortage, location_id))
                    print(f"DEBUG: Created backorder for product {pid} at location {location_id}: shortage {shortage}")
                else:
                    print(f"DEBUG: Product {pid} fully fulfilled at location {location_id}")
            else:
                cursor.execute('''
                    INSERT INTO backorder (order_id, product_id, requested_qty, available_qty, shortage, status, location_id)
                    VALUES (?, ?, ?, ?, ?, 'pending', ?)
                ''', (order_id, pid, qty, 0, qty, location_id))
                print(f"DEBUG: No inventory at location {location_id} for product {pid}; created backorder qty {qty}")

        conn.commit()
        conn.close()

        if available_locations:
            flash('Order submitted successfully!', 'success')
            location_names = [name for _, name in available_locations]
            flash('Items available at: ' + ', '.join(location_names), 'info')
        else:
            flash('Order submitted successfully!', 'success')
            flash('No single branch currently stocks all selected items. Consider checking multiple branches.', 'warning')

        return redirect(url_for('customer_dashboard'))
        
    except Exception as e:
        print(f"Error submitting order: {str(e)}")
        traceback.print_exc()
        flash('Error submitting order. Please try again.', 'error')
        return redirect(url_for('customer_dashboard'))


@app.route('/delete_order/<int:order_id>', methods=['POST'])
def delete_order(order_id):
    """Allow customers to delete their own orders"""
    if 'user_id' not in session or session.get('user_type') != 'customer':
        flash('Please log in to access your dashboard.', 'warning')
        return redirect(url_for('login'))
    
    customer_id = session['user_id']
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT order_id FROM cust_order WHERE order_id = ? AND customer_id = ?', 
                      (order_id, customer_id))
        order = cursor.fetchone()
        
        if order:
            cursor.execute('DELETE FROM cust_order WHERE order_id = ?', (order_id,))
            conn.commit()
            flash('Order deleted successfully!', 'success')
        else:
            flash('Order not found or you do not have permission to delete it.', 'error')
        
        conn.close()
        
    except Exception as e:
        flash('Error deleting order. Please try again.', 'error')
        print(f"Error deleting order: {str(e)}")
    
    return redirect(url_for('customer_dashboard'))


@app.route('/inventory')
def inventory():
    if 'user_id' not in session or session.get('user_type') != 'staff':
        flash('Please log in to access inventory.', 'warning')
        return redirect(url_for('verify_staff'))
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            l.location_id,
            l.location_name,
            np.product_id,
            np.product_name,
            c.category_name,
            IFNULL(SUM(ui.quantity), 0) as quantity
        FROM location l
        CROSS JOIN new_product np
        LEFT JOIN categories c ON np.category_id = c.category_id
        LEFT JOIN update_inventory ui ON np.product_id = ui.product_id AND l.location_id = ui.location_id
        GROUP BY l.location_id, l.location_name, np.product_id, np.product_name, c.category_name
        ORDER BY l.location_id, c.category_name, np.product_name
    ''')
    all_rows = cursor.fetchall()
    
    locations_inventory = {}
    for row in all_rows:
        loc_id = row['location_id']
        if loc_id not in locations_inventory:
            locations_inventory[loc_id] = {
                'location_name': row['location_name'],
                'products': []
            }
        locations_inventory[loc_id]['products'].append(row)
    
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
    totals = cursor.fetchall()
    
    conn.close()
    return render_template('inventory.html', locations_inventory=locations_inventory, totals=totals)




@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        product_name = request.form.get('product-name')
        product_id = request.form.get('product-id')
        min_qty = request.form.get('min-quantity')
        max_qty = request.form.get('max-quantity')
        category = request.form.get('Categorie')
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
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
    
    return render_template('inventory_products.html')


@app.route('/view_inventory')
def view_inventory():
    conn = sqlite3.connect(db_path)
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
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        locations = cursor.execute('SELECT location_id, location_name FROM location ORDER BY location_id').fetchall()
        
        cursor.execute('''
            SELECT 
                l.location_id,
                l.location_name,
                np.product_id,
                np.product_name,
                c.category_name,
                IFNULL(SUM(ui.quantity), 0) as quantity
            FROM location l
            CROSS JOIN new_product np
            LEFT JOIN categories c ON np.category_id = c.category_id
            LEFT JOIN update_inventory ui ON np.product_id = ui.product_id AND l.location_id = ui.location_id
            GROUP BY l.location_id, l.location_name, np.product_id, np.product_name, c.category_name
            ORDER BY l.location_id, c.category_name, np.product_name
        ''')
        location_products = cursor.fetchall()
        
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
        totals = cursor.fetchall()
        conn.close()

        pdf = FPDF()
        pdf.add_page('L')

        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'GrocerEase Inventory Report', 0, 1, 'C')
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 10, f'Generated on {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 1, 'C')
        pdf.ln(10)

        col_widths = [30, 100, 80, 40]
        headers = ['ID', 'Product Name', 'Category', 'Quantity']

        def draw_table(pdf, col_widths, headers, products, location_name=None):
            if location_name:
                pdf.set_font('Arial', 'B', 13)
                pdf.cell(0, 10, location_name, 0, 1)
                pdf.ln(5)
            
            pdf.set_font('Arial', 'B', 12)
            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 10, header, 1)
            pdf.ln()

            pdf.set_font('Arial', '', 11)
            for product in products:
                qty = product['quantity'] if product['quantity'] is not None else 0
                low_stock = qty < 10
                if low_stock:
                    pdf.set_fill_color(255, 165, 0)
                    fill_flag = True
                else:
                    pdf.set_fill_color(255, 255, 255)
                    fill_flag = False

                pdf.cell(col_widths[0], 10, str(product['product_id']), 1, 0, '', fill_flag)
                pdf.cell(col_widths[1], 10, str(product['product_name']), 1, 0, '', fill_flag)
                pdf.cell(col_widths[2], 10, str(product['category_name']), 1, 0, '', fill_flag)
                pdf.cell(col_widths[3], 10, str(qty), 1, 0, '', fill_flag)
                pdf.ln()
            
            pdf.ln(8)

        for loc in locations:
            loc_products = [p for p in location_products if p['location_id'] == loc['location_id']]
            draw_table(pdf, col_widths, headers, loc_products, loc['location_name'])

        pdf.set_font('Arial', 'B', 13)
        pdf.cell(0, 10, 'TOTAL INVENTORY (ALL LOCATIONS)', 0, 1)
        pdf.ln(5)
        draw_table(pdf, col_widths, headers, totals, None)

        pdf_buffer = io.BytesIO()

        pdf_out = pdf.output(dest='S')
        if isinstance(pdf_out, (bytes, bytearray)):
            pdf_bytes = bytes(pdf_out)
        elif isinstance(pdf_out, str):
            try:
                pdf_bytes = pdf_out.encode('latin-1')
            except Exception:
                pdf_bytes = pdf_out.encode('utf-8', errors='replace')
        else:
            try:
                pdf_bytes = str(pdf_out).encode('utf-8', errors='replace')
            except Exception:
                pdf_bytes = b''

        pdf_buffer.write(pdf_bytes)
        pdf_buffer.seek(0)

        filename = f'inventory_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        try:
            return send_file(
                pdf_buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=filename
            )
        except TypeError:
            return send_file(
                pdf_buffer,
                mimetype='application/pdf',
                as_attachment=True,
                attachment_filename=filename
            )
                
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        traceback.print_exc()
        return "Error generating PDF", 500

@app.route('/staff')
def staff():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    low_stock_rows = cursor.execute(
        '''
        SELECT np.product_id, np.product_name, IFNULL(SUM(ui.quantity), 0) AS total_qty
        FROM new_product np
        LEFT JOIN update_inventory ui ON np.product_id = ui.product_id
        GROUP BY np.product_id, np.product_name
        HAVING total_qty < 10
        ORDER BY total_qty ASC
        '''
    ).fetchall()

    cursor.execute('''
        UPDATE backorder
        SET status = 'pending'
        WHERE status = 'fulfilled' AND shortage > 0
    ''')
    
    backorder_rows = cursor.execute(
        '''
         SELECT b.backorder_id, b.order_id, b.product_id, np.product_name, 
             b.requested_qty, b.available_qty, b.shortage, b.status,
             c.cust_name, c.cust_surname, b.location_id, 
             COALESCE(l.location_name, 'Not Specified') as location_name
         FROM backorder b
         JOIN new_product np ON b.product_id = np.product_id
         JOIN cust_order co ON b.order_id = co.order_id
         JOIN customer c ON co.customer_id = c.customer_id
         LEFT JOIN location l ON b.location_id = l.location_id
         WHERE b.status = 'pending'
         ORDER BY b.backorder_id DESC
        '''
    ).fetchall()

    products = cursor.execute(
        'SELECT product_id, product_name FROM new_product ORDER BY product_name'
    ).fetchall()

    row = cursor.execute('SELECT MAX(order_id) as last_id FROM cust_order').fetchone()
    total_orders = row['last_id'] if row and row['last_id'] is not None else 0

    conn.close()
    return render_template('Staff.html', low_stock_items=low_stock_rows, backorders=backorder_rows, products=products, total_orders=total_orders)

@app.route('/update_inventory', methods=['POST'])
def update_inventory():
    if 'user_id' not in session or session.get('user_type') != 'staff':
        flash('Please log in as staff to update inventory.', 'warning')
        return redirect(url_for('verify_staff'))
    
    try:
        product_id = int(request.form.get('product_id'))
        quantity = int(request.form.get('quantity'))
        location_id = int(request.form.get('location'))

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        prod_row = cursor.execute('SELECT category_id FROM new_product WHERE product_id = ?', (product_id,)).fetchone()
        category_id = prod_row[0] if prod_row else None

        cursor.execute(
            '''
            INSERT INTO update_inventory (quantity, product_id, location_id, staff_id, category_id)
            VALUES (?, ?, ?, ?, ?)
            ''',
            (quantity, product_id, location_id, session.get('user_id', 1), category_id)
        )

        stock_to_allocate = quantity
        inserted_update_id = cursor.lastrowid

        backorder_rows = cursor.execute('''
            SELECT backorder_id, requested_qty, available_qty, shortage, location_id
            FROM backorder
            WHERE product_id = ? AND status = 'pending' AND (location_id = ? OR location_id IS NULL)
            ORDER BY backorder_id
        ''', (product_id, location_id)).fetchall()

        for bo in backorder_rows:
            if stock_to_allocate <= 0:
                break
            bo_id = bo['backorder_id']
            bo_shortage = bo['shortage'] if bo['shortage'] is not None else (bo['requested_qty'] - (bo['available_qty'] or 0))
            allocate = min(stock_to_allocate, bo_shortage)
            if allocate <= 0:
                continue

            new_shortage = bo_shortage - allocate
            new_available = (bo['available_qty'] or 0) + allocate
            new_status = 'fulfilled' if new_shortage <= 0 else 'pending'

            cursor.execute('''
                UPDATE backorder
                SET available_qty = ?, shortage = ?, status = ?
                WHERE backorder_id = ?
            ''', (new_available, new_shortage, new_status, bo_id))

            print(f"DEBUG: Allocated {allocate} to backorder {bo_id} for product {product_id} at location {location_id} (remaining stock_to_allocate: {stock_to_allocate - allocate})")

            stock_to_allocate -= allocate

        allocated_amount = quantity - stock_to_allocate
        if allocated_amount > 0:
            remaining_qty = quantity - allocated_amount
            cursor.execute('''
                UPDATE update_inventory
                SET quantity = ?
                WHERE update_id = ?
            ''', (remaining_qty, inserted_update_id))


        conn.commit()
        conn.close()

        return redirect(url_for('inventory'))

    except Exception as e:
        print(f"Error updating inventory: {str(e)}")
        traceback.print_exc()
        return "Error updating inventory", 500


@app.route('/verify_staff', methods=['GET', 'POST'])
def verify_staff():
    if request.method == 'POST':
        staff_id = request.form.get('staff-id')
        password = request.form.get('password')
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM staff WHERE staff_id = ? AND staff_password = ?', (staff_id, password))
        staff = cursor.fetchone()
        conn.close()
        
        if staff:
            session['user_id'] = staff['staff_id']
            session['user_name'] = f"{staff['staff_name']} {staff['staff_surname']}"
            session['user_type'] = 'staff'
            return redirect(url_for('staff'))
        else:
            flash('Invalid staff ID or password. Please try again.', 'error')
            return redirect(url_for('verify_staff'))
    
    return render_template('Verification.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
