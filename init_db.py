import sqlite3
from werkzeug.security import generate_password_hash
from config import DATABASE_PATH

def init_database():
    print("Connecting to database...")
    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    # ==========================================
    # 1. TABLE CREATION
    # ==========================================
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL 
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, 
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_number TEXT UNIQUE NOT NULL,
            room_type TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT, 
            status TEXT DEFAULT 'Available'
        )
    ''')

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

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            room_id INTEGER NOT NULL,
            rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
            comment TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers (id),
            FOREIGN KEY (room_id) REFERENCES rooms (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL, 
            message TEXT NOT NULL,
            is_from_admin BOOLEAN DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # ==========================================
    # 2. MASSIVE DUMMY DATA INJECTION
    # ==========================================
    print("Injecting massive sample data...")
    
    # --- USERS ---
    admin_pw = generate_password_hash('admin123')
    staff_pw = generate_password_hash('staff123')
    guest_pw = generate_password_hash('guest123')
    
    cursor.execute("INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)", ('admin', admin_pw, 'Admin'))
    cursor.execute("INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)", ('desk_staff', staff_pw, 'Staff'))
    cursor.execute("INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)", ('online_guest', guest_pw, 'Guest'))
    
    extra_users = [
        ('michael_scott', guest_pw, 'Guest'), ('sarah_connor', guest_pw, 'Guest'),
        ('bruce_wayne', guest_pw, 'Guest'), ('tony_stark', guest_pw, 'Guest'), ('clark_kent', guest_pw, 'Guest')
    ]
    cursor.executemany("INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)", extra_users)

    # --- CUSTOMERS ---
    sample_customers = [
        (3, 'Mohamed Matrouh', '+86 135 1234 5678', 'mohamed@example.com'),
        (4, 'Michael Scott', '+1 570 555 1234', 'michael.s@dundermifflin.com'),
        (5, 'Sarah Connor', '+1 213 555 9876', 's.connor@sky.net'),
        (6, 'Bruce Wayne', '+1 212 555 0001', 'bwayne@wayneenterprises.com'),
        (7, 'Tony Stark', '+1 310 555 9999', 'tony@starkindustries.com'),
        (8, 'Clark Kent', '+1 212 555 3456', 'ckent@dailyplanet.com'),
        (None, 'James Bond', '+44 20 7946 0007', '007@mi6.gov.uk'),
        (None, 'John Doe', '+86 138 0000 0000', 'johndoe@example.com'),
        (None, 'Jane Smith', '+44 1632 960123', 'jane.smith@example.com'),
        (None, 'Jackie Chan', '+852 9876 5432', 'jackie@example.hk')
    ]
    cursor.executemany("INSERT OR IGNORE INTO customers (user_id, full_name, phone, email) VALUES (?, ?, ?, ?)", sample_customers)

    # --- ROOMS (100 ROOM INVENTORY GENERATOR) ---
    sample_rooms = []
    
    # Floors 1 & 2: 40 Deluxe Single Rooms ($80/night)
    for floor in [1, 2]:
        for i in range(1, 21):
            room_num = f"{floor}{i:02d}"  # Creates 101, 102... 220
            sample_rooms.append((room_num, 'Single', 80.0, 'Cozy single room with a city view, premium minibar, and high-speed Wi-Fi.', 'Available'))
            
    # Floors 3 & 4: 40 Premium Double Rooms ($140/night)
    for floor in [3, 4]:
        for i in range(1, 21):
            room_num = f"{floor}{i:02d}"
            # Throw two rooms into Maintenance for realism
            status = 'Maintenance' if room_num in ['310', '405'] else 'Available'
            sample_rooms.append((room_num, 'Double', 140.0, 'Spacious double room perfect for couples, featuring a king-size bed and smart TV.', status))
            
    # Floor 5: 20 Executive Suites ($250/night)
    for i in range(1, 21):
        room_num = f"5{i:02d}"
        # Throw two rooms into Occupied for realism
        status = 'Occupied' if room_num in ['501', '502'] else 'Available'
        sample_rooms.append((room_num, 'Suite', 250.0, 'Luxury suite with a private balcony, ocean view, and 24/7 room service.', status))

    cursor.executemany("INSERT OR IGNORE INTO rooms (room_number, room_type, price, description, status) VALUES (?, ?, ?, ?, ?)", sample_rooms)

    # Commit changes and close
    connection.commit()
    connection.close()
    print("100-Room Mega-Hotel Database initialized successfully! 🚀")

if __name__ == '__main__':
    init_database()