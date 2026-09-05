# fix_db.py - Run this to fix database issues
import sqlite3
import os

def fix_database():
    """Fix database by recreating all tables"""
    
    # Delete old database
    if os.path.exists('instance/vehicle_management.db'):
        os.remove('instance/vehicle_management.db')
        print("Deleted old database")
    
    # Create new database
    conn = sqlite3.connect('instance/vehicle_management.db')
    cursor = conn.cursor()
    
    # Read schema file
    with open('database/schema.sql', 'r') as f:
        schema = f.read()
    
    # Execute schema
    cursor.executescript(schema)
    conn.commit()
    
    # Verify users table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if cursor.fetchone():
        print("✓ Users table created successfully")
    else:
        print("✗ Failed to create users table")
    
    # Check if admin user exists
    cursor.execute("SELECT * FROM users WHERE username='admin'")
    admin = cursor.fetchone()
    if admin:
        print(f"✓ Admin user exists: {admin[1]}")
    else:
        print("✗ Admin user not found")
    
    conn.close()
    print("\nDatabase fixed successfully!")
    print("You can now run: python app.py")
    print("Login with: admin / admin123")

if __name__ == '__main__':
    fix_database()