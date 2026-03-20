import sqlite3
from werkzeug.security import generate_password_hash
from config import DATABASE_PATH

def init_database():
    print("Connecting to database...")
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    # 1. Create Users Table (For hotel staff)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')

    # 2. Create Customers Table (For hotel guests)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT
        )
    ''')

    # 3. Create Rooms Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_number TEXT UNIQUE NOT NULL,
            room_type TEXT NOT NULL,
            price REAL NOT NULL,
            status TEXT DEFAULT 'Available'
        )
    ''')

    # 4. Create Bookings Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            room_id INTEGER NOT NULL,
            check_in_date TEXT NOT NULL,
            check_out_date TEXT NOT NULL,
            status TEXT DEFAULT 'Confirmed',
            FOREIGN KEY (customer_id) REFERENCES customers (id),
            FOREIGN KEY (room_id) REFERENCES rooms (id)
        )
    ''')

    # --- INJECT DUMMY DATA ---
    print("Injecting sample data...")
    
    # Add an Admin and a Staff user (Passwords are securely hashed!)
    admin_password = generate_password_hash('admin123')
    staff_password = generate_password_hash('staff123')
    cursor.execute("INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)", ('admin', admin_password, 'Admin'))
    cursor.execute("INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)", ('desk_staff', staff_password, 'Staff'))

    # Add Sample Rooms
    sample_rooms = [
        ('101', 'Single', 80.0, 'Available'),
        ('102', 'Double', 120.0, 'Available'),
        ('201', 'Suite', 250.0, 'Occupied'),
        ('202', 'Suite', 250.0, 'Maintenance')
    ]
    cursor.executemany("INSERT OR IGNORE INTO rooms (room_number, room_type, price, status) VALUES (?, ?, ?, ?)", sample_rooms)

    # Add a Sample Customer
    cursor.execute("INSERT OR IGNORE INTO customers (full_name, phone, email) VALUES (?, ?, ?)", ('John Doe', '555-0198', 'john@example.com'))

    # Commit changes and close
    connection.commit()
    connection.close()
    print("Database initialized successfully! 🚀")

if __name__ == '__main__':
    init_database()