import sqlite3
from config import DATABASE_PATH

def sync_database_statuses():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    print("Syncing database statuses...")
    
    # This logic looks at any booking that is NOT 'Confirmed', 'Checked-In', or 'Completed'
    # and ensures the database knows it's effectively a Refund/Cancel.
    # This cleans up all those "blank" statuses you were seeing.
    cursor.execute("""
        UPDATE bookings 
        SET status = 'Refunded' 
        WHERE status NOT IN ('Confirmed', 'Checked-In', 'Completed') 
        OR status IS NULL
    """)
    
    conn.commit()
    count = cursor.rowcount
    conn.close()
    
    print(f"Sync complete! Updated {count} stale booking records to 'Refunded'.")

if __name__ == '__main__':
    sync_database_statuses()