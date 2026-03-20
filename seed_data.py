import sqlite3
import random
from datetime import datetime, timedelta

# Connect to your existing database
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

print("🧹 Clearing old dummy data...")
cursor.execute("DELETE FROM bookings")
cursor.execute("DELETE FROM rooms")
cursor.execute("DELETE FROM customers")

print("🚪 Generating 40 Premium Rooms...")
room_types = ['Single', 'Double', 'Suite']
for i in range(101, 141):
    rtype = random.choice(room_types)
    price = 99.99 if rtype == 'Single' else 149.99 if rtype == 'Double' else 299.99
    # Make a few rooms occupied or under maintenance
    status = random.choices(['Available', 'Occupied', 'Maintenance'], weights=[70, 20, 10])[0]
    cursor.execute("INSERT INTO rooms (room_number, room_type, price, status) VALUES (?, ?, ?, ?)", 
                   (str(i), rtype, price, status))

print("👥 Generating 75 VIP Guests...")
first_names = ['James', 'Mary', 'Robert', 'Patricia', 'John', 'Jennifer', 'Michael', 'Linda', 'David', 'Elizabeth', 'William', 'Barbara', 'Richard', 'Susan', 'Joseph', 'Jessica', 'Thomas', 'Sarah', 'Charles', 'Karen', 'Wei', 'Jian', 'Ming', 'Li', 'Hua']
last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez', 'Wang', 'Li', 'Zhang', 'Liu', 'Chen']

for _ in range(75):
    name = f"{random.choice(first_names)} {random.choice(last_names)}"
    phone = f"+1 (555) {random.randint(100, 999)}-{random.randint(1000, 9999)}"
    email = f"{name.lower().replace(' ', '.')}@example.com"
    cursor.execute("INSERT INTO customers (full_name, phone, email) VALUES (?, ?, ?)", (name, phone, email))

print("📅 Generating 150 Realistic Bookings...")
cursor.execute("SELECT id FROM rooms")
room_ids = [row[0] for row in cursor.fetchall()]

cursor.execute("SELECT id FROM customers")
customer_ids = [row[0] for row in cursor.fetchall()]

statuses = ['Confirmed', 'Checked-In', 'Completed', 'Cancelled']

for _ in range(150):
    c_id = random.choice(customer_ids)
    r_id = random.choice(room_ids)
    
    # Generate random dates around today
    days_offset = random.randint(-30, 30)
    stay_length = random.randint(1, 7)
    
    check_in = datetime.now() + timedelta(days=days_offset)
    check_out = check_in + timedelta(days=stay_length)
    
    # Logic to make status match the dates
    if check_out < datetime.now():
        status = 'Completed'
    elif check_in <= datetime.now() <= check_out:
        status = 'Checked-In'
    elif check_in > datetime.now():
        status = random.choices(['Confirmed', 'Cancelled'], weights=[90, 10])[0]
    else:
        status = random.choice(statuses)

    cursor.execute("""
        INSERT INTO bookings (customer_id, room_id, check_in_date, check_out_date, status) 
        VALUES (?, ?, ?, ?, ?)
    """, (c_id, r_id, check_in.strftime('%Y-%m-%d'), check_out.strftime('%Y-%m-%d'), status))

conn.commit()
conn.close()
print("✅ Success! Database is now packed with enterprise-level data.")