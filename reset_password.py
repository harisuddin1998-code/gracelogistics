# reset_password.py - Run this to fix admin password
import sqlite3
import hashlib
import secrets
import os

def reset_admin_password():
    """Reset admin password to 'admin123'"""
    
    # Ensure instance directory exists
    os.makedirs('instance', exist_ok=True)
    
    # Connect to database
    conn = sqlite3.connect('instance/vehicle_management.db')
    cursor = conn.cursor()
    
    # Create a proper password hash for 'admin123'
    password = 'admin123'
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    stored_hash = f"pbkdf2:sha256:100000${salt}${password_hash.hex()}"
    
    # Update or insert admin user
    try:
        # First check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("Users table doesn't exist! Creating...")
            cursor.execute('''
                CREATE TABLE users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    full_name TEXT NOT NULL,
                    role TEXT DEFAULT 'staff',
                    is_active INTEGER DEFAULT 1,
                    last_login DATETIME,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        
        # Insert or replace admin user
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, username, email, password_hash, full_name, role, is_active)
            VALUES (1, 'admin', 'admin@vehicle.com', ?, 'System Administrator', 'admin', 1)
        ''', (stored_hash,))
        
        conn.commit()
        print("✓ Admin password reset successfully!")
        print("✓ Username: admin")
        print("✓ Password: admin123")
        
        # Verify the user exists
        cursor.execute("SELECT user_id, username, role FROM users WHERE username='admin'")
        user = cursor.fetchone()
        if user:
            print(f"✓ Verification: User found - ID: {user[0]}, Username: {user[1]}, Role: {user[2]}")
        else:
            print("✗ Verification failed - User not found")
            
    except Exception as e:
        print(f"Error: {e}")
    
    conn.close()

if __name__ == '__main__':
    reset_admin_password()