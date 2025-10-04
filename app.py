from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import hashlib
from datetime import datetime
import os
# hello

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'

# Database initialization
def init_db():
    conn = sqlite3.connect('car_rental.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            phone_number TEXT,
            role TEXT DEFAULT 'customer'
        )
    ''')
    
    # Cars table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT NOT NULL,
            model TEXT NOT NULL,
            year INTEGER NOT NULL,
            price_per_hour REAL NOT NULL,
            available BOOLEAN DEFAULT TRUE,
            image_url TEXT,
            vehicle_type TEXT
        )
    ''')
    
    # Bookings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            car_id INTEGER,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            total_cost REAL NOT NULL,
            status TEXT DEFAULT 'confirmed',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (car_id) REFERENCES cars (id)
        )
    ''')
    
    # Insert sample car data
    sample_cars = [
    ('Toyota', 'Camry', 2022, 25.0, True, 'https://images.unsplash.com/photo-1657872737697-737a2d123ef2?q=80&w=1740&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D', 'Sedan'),
    ('BMW', 'M4', 2025, 25.0, True, 'https://images.unsplash.com/photo-1660310477229-d03d8565f15d?q=80&w=1740&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D', 'Sports'),
    ('Honda', 'Civic', 2021, 22.0, True, 'https://images.unsplash.com/photo-1594070319944-7c0cbebb6f58?q=80&w=1600&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D', 'Sedan'),
    ('Ford', 'Mustang', 2023, 45.0, True, 'https://images.unsplash.com/photo-1625231334168-35067f8853ed?q=80&w=774&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D', 'Sports'),
    ('BMW', 'X5', 2022, 55.0, True, 'https://images.unsplash.com/photo-1635089917414-6da790da8479?q=80&w=774&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D', 'SUV'),
    ('Tesla', 'Model 3', 2023, 35.0, True, 'https://images.unsplash.com/photo-1560958089-b8a1929cea89?q=80&w=1742&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D', 'Electric'),
    ('Nissan', 'Altima', 2021, 24.0, True, 'https://images.unsplash.com/photo-1581540222194-0def2dda95b8?q=80&w=1740&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D', 'Sedan'),
    ('Jeep', 'Wrangler', 2023, 40.0, True, 'https://images.unsplash.com/photo-1602038187784-41e649a79d38?q=80&w=1740&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D', 'SUV'),
    ('Mercedes', 'C-Class', 2022, 50.0, True, 'https://images.unsplash.com/photo-1686562483617-3cf08d81e117?q=80&w=1740&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D', 'Luxury')
]


    
    cursor.execute('SELECT COUNT(*) FROM cars')
    if cursor.fetchone()[0] == 0:
        cursor.executemany('INSERT INTO cars (brand, model, year, price_per_hour, available, image_url, vehicle_type) VALUES (?, ?, ?, ?, ?, ?, ?)', sample_cars)
    
    # Create admin account
    cursor.execute('SELECT COUNT(*) FROM users WHERE role = "admin"')
    if cursor.fetchone()[0] == 0:
        admin_password = hashlib.sha256('admin123'.encode()).hexdigest()
        cursor.execute('INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)', 
                      ('admin', 'admin@carrental.com', admin_password, 'admin'))
   
    conn.commit()
    conn.close()

# Helper functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_db_connection():
    conn = sqlite3.connect('car_rental.db')
    conn.row_factory = sqlite3.Row
    return conn

# Routes
@app.route('/')
def index():
    conn = get_db_connection()
    
    # Get filter parameters
    vehicle_type = request.args.get('vehicle_type', '')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    
    # Build query
    query = 'SELECT * FROM cars WHERE available = TRUE'
    params = []
    
    if vehicle_type:
        query += ' AND vehicle_type = ?'
        params.append(vehicle_type)
    
    if min_price is not None:
        query += ' AND price_per_hour >= ?'
        params.append(min_price)
    
    if max_price is not None:
        query += ' AND price_per_hour <= ?'
        params.append(max_price)
    
    cars = conn.execute(query, params).fetchall()
    vehicle_types = conn.execute('SELECT DISTINCT vehicle_type FROM cars').fetchall()
    
    conn.close()
    return render_template('index.html', cars=cars, vehicle_types=vehicle_types)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        phone = request.form.get('phone', '')
        
        if not all([username, email, password]):
            flash('Username, email and password are required!', 'error')
            return render_template('register.html')
        
        conn = get_db_connection()
        
        # Check if user exists
        existing_user = conn.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email)).fetchone()
        if existing_user:
            flash('Username or email already exists!', 'error')
            conn.close()
            return render_template('register.html')
        
        # Create new user
        password_hash = hash_password(password)
        conn.execute('INSERT INTO users (username, email, password_hash, phone_number) VALUES (?, ?, ?, ?)',
                    (username, email, password_hash, phone))
        conn.commit()
        conn.close()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and user['password_hash'] == hash_password(password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            
            flash(f'Welcome back, {user["username"]}!', 'success')
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Successfully logged out', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please login first', 'error')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    bookings = conn.execute('''
        SELECT b.*, c.brand, c.model, c.year 
        FROM bookings b
        JOIN cars c ON b.car_id = c.id
        WHERE b.user_id = ?
        ORDER BY b.created_at DESC
    ''', (session['user_id'],)).fetchall()
    conn.close()
    
    return render_template('dashboard.html', bookings=bookings)

@app.route('/book/<int:car_id>', methods=['GET', 'POST'])
def book_car(car_id):
    if 'user_id' not in session:
        flash('Please login first to book a car', 'error')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    car = conn.execute('SELECT * FROM cars WHERE id = ? AND available = TRUE', (car_id,)).fetchone()
    
    if not car:
        flash('Car not available!', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        
        # Calculate total cost (simplified - hours between dates)
        try:
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)
            
            if end <= start:
                flash('Return time must be after pickup time!', 'error')
                return render_template('book.html', car=car)
            
            hours = (end - start).total_seconds() / 3600
            total_cost = hours * car['price_per_hour']
            
            # Create booking
            conn.execute('''
                INSERT INTO bookings (user_id, car_id, start_date, end_date, total_cost)
                VALUES (?, ?, ?, ?, ?)
            ''', (session['user_id'], car_id, start_date, end_date, total_cost))
            
            conn.commit()
            conn.close()
            
            flash(f'Booking confirmed! Total cost: ${total_cost:.2f}', 'success')
            return redirect(url_for('dashboard'))
            
        except ValueError:
            flash('Invalid date format!', 'error')
    
    conn.close()
    return render_template('book.html', car=car)

@app.route('/admin')
def admin_dashboard():
    if 'role' not in session or session['role'] != 'admin':
        flash('Admin access required!', 'error')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cars = conn.execute('SELECT * FROM cars ORDER BY id DESC').fetchall()
    bookings = conn.execute('''
        SELECT b.*, c.brand, c.model, u.username 
        FROM bookings b
        JOIN cars c ON b.car_id = c.id
        JOIN users u ON b.user_id = u.id
        ORDER BY b.created_at DESC
        LIMIT 20
    ''').fetchall()
    conn.close()
    
    return render_template('admin.html', cars=cars, bookings=bookings)

@app.route('/admin/add_car', methods=['POST'])
def add_car():
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    brand = request.form['brand']
    model = request.form['model']
    year = int(request.form['year'])
    price = float(request.form['price'])
    vehicle_type = request.form['vehicle_type']
    
    conn = get_db_connection()
    conn.execute('INSERT INTO cars (brand, model, year, price_per_hour, vehicle_type, image_url) VALUES (?, ?, ?, ?, ?, ?)',
                (brand, model, year, price, vehicle_type, f'https://via.placeholder.com/300x200?text={brand}+{model}'))
    conn.commit()
    conn.close()
    
    flash(f'Successfully added {brand} {model}!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/toggle_car/<int:car_id>')
def toggle_car_availability(car_id):
    if 'role' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    car = conn.execute('SELECT available FROM cars WHERE id = ?', (car_id,)).fetchone()
    new_status = not car['available']
    
    conn.execute('UPDATE cars SET available = ? WHERE id = ?', (new_status, car_id))
    conn.commit()
    conn.close()
    
    status_text = "enabled" if new_status else "disabled"
    flash(f'Car {status_text} successfully', 'success')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    init_db()
    print("🚗 Car Rental System starting...")
    print("🌐 Access at: http://localhost:5000")
    print("👤 Admin account: admin / admin123")
    app.run(debug=True, port=5000)