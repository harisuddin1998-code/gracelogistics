import sqlite3
import os

DB_PATH = 'instance/vehicle_management.db'

def get_db_connection():
    """Create and return database connection"""
    os.makedirs('instance', exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize database with schema"""
    os.makedirs('instance', exist_ok=True)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Read and execute schema.sql
    schema_path = 'database/schema.sql'
    if os.path.exists(schema_path):
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
            # Split by semicolon and execute each statement
            statements = schema_sql.split(';')
            for statement in statements:
                if statement.strip():
                    try:
                        cursor.execute(statement)
                    except Exception as e:
                        print(f"Warning: {e}")
        conn.commit()
        print("Database schema created successfully!")
    else:
        print(f"Schema file not found at {schema_path}")
    
    # Verify users table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if not cursor.fetchone():
        print("ERROR: Users table was not created!")
    
    conn.close()
    print("Database initialized successfully!")

def backup_database():
    """Backup database"""
    import shutil
    from datetime import datetime
    
    os.makedirs('backups', exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'backups/vehicle_management_backup_{timestamp}.db'
    
    if os.path.exists(DB_PATH):
        shutil.copy2(DB_PATH, backup_file)
        return backup_file
    return None