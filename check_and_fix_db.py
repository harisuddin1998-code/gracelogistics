import sqlite3
import os

def check_and_fix_database():
    db_path = 'instance/vehicle_management.db'
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("DATABASE SCHEMA CHECK")
    print("=" * 60)
    
    # Check driver_advances table
    print("\n1. Checking driver_advances table...")
    cursor.execute("PRAGMA table_info(driver_advances)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"   Existing columns: {', '.join(columns)}")
    
    if 'deduction_month' not in columns:
        print("   Adding deduction_month column...")
        cursor.execute("ALTER TABLE driver_advances ADD COLUMN deduction_month TEXT")
        print("   ✓ deduction_month column added")
    else:
        print("   ✓ deduction_month column already exists")
    
    # Check drivers table
    print("\n2. Checking drivers table...")
    cursor.execute("PRAGMA table_info(drivers)")
    driver_columns = [col[1] for col in cursor.fetchall()]
    print(f"   Existing columns: {', '.join(driver_columns)}")
    
    if 'advance_balance' not in driver_columns:
        print("   Adding advance_balance column...")
        cursor.execute("ALTER TABLE drivers ADD COLUMN advance_balance REAL DEFAULT 0")
        print("   ✓ advance_balance column added")
    else:
        print("   ✓ advance_balance column already exists")
    
    # Check if there are any pending advances that need to be synced
    print("\n3. Syncing advance balances...")
    cursor.execute('''
        SELECT d.driver_id, d.full_name, COALESCE(SUM(a.amount), 0) as total_advance
        FROM drivers d
        LEFT JOIN driver_advances a ON d.driver_id = a.driver_id AND a.status = 'Pending'
        GROUP BY d.driver_id
    ''')
    
    advances = cursor.fetchall()
    updated_count = 0
    
    for advance in advances:
        driver_id = advance[0]
        total = advance[2] if advance[2] else 0
        cursor.execute("UPDATE drivers SET advance_balance = ? WHERE driver_id = ?", (total, driver_id))
        updated_count += 1
    
    print(f"   ✓ Synced advance balances for {updated_count} drivers")
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 60)
    print("DATABASE CHECK COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("\nYour database is ready for advance salary features!")
    print("You can now run: python app.py")

if __name__ == '__main__':
    check_and_fix_database()