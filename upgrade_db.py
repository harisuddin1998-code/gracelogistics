# upgrade_db.py - Safe database upgrade
import sqlite3
import os

def upgrade_database():
    conn = sqlite3.connect('instance/vehicle_management.db')
    cursor = conn.cursor()
    
    print("Starting database upgrade...")
    
    # ============================================
    # Check and upgrade maintenance table
    # ============================================
    cursor.execute("PRAGMA table_info(maintenance)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'maintenance_type' not in columns:
        print("Adding new columns to maintenance table...")
        # Rename old table
        cursor.execute("ALTER TABLE maintenance RENAME TO maintenance_old")
        
        # Create new maintenance table
        cursor.execute('''
            CREATE TABLE maintenance (
                maintenance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER NOT NULL,
                maintenance_type TEXT NOT NULL,
                date DATE NOT NULL,
                cost DECIMAL(10,2),
                quantity INTEGER DEFAULT 1,
                unit_price DECIMAL(10,2),
                next_due_km INTEGER,
                next_due_date DATE,
                mechanic_name TEXT,
                notes TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Copy data from old table
        cursor.execute('''
            INSERT INTO maintenance (maintenance_id, vehicle_id, maintenance_type, date, cost, 
                                    next_due_km, next_due_date, mechanic_name, notes, created_at)
            SELECT maintenance_id, vehicle_id, type, date, cost, 
                   next_due_km, next_due_date, mechanic_name, notes, created_at
            FROM maintenance_old
        ''')
        
        # Drop old table
        cursor.execute("DROP TABLE maintenance_old")
        print("  - Maintenance table upgraded")
    
    # ============================================
    # Create Tuning table
    # ============================================
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tuning'")
    if not cursor.fetchone():
        cursor.execute('''
            CREATE TABLE tuning (
                tuning_id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER NOT NULL,
                date DATE NOT NULL,
                tuning_type TEXT CHECK(tuning_type IN ('Engine Tuning', 'ECU Remap', 'Performance Tuning', 'Fuel System Tuning')),
                cost DECIMAL(10,2),
                technician_name TEXT,
                before_performance TEXT,
                after_performance TEXT,
                notes TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("  - Tuning table created")
    
    # ============================================
    # Create Electrical Work table
    # ============================================
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='electrical_work'")
    if not cursor.fetchone():
        cursor.execute('''
            CREATE TABLE electrical_work (
                electrical_id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER NOT NULL,
                date DATE NOT NULL,
                work_type TEXT CHECK(work_type IN (
                    'Wiring Repair', 'Lighting System', 'Battery Replacement', 'Alternator Repair',
                    'Starter Motor', 'Fuse Box', 'Sensors', 'Dashboard Repair', 'AC Electrical', 'Complete Wiring'
                )),
                cost DECIMAL(10,2),
                technician_name TEXT,
                parts_used TEXT,
                hours_spent DECIMAL(4,2),
                notes TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("  - Electrical work table created")
    
    # ============================================
    # Create Body Work table
    # ============================================
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='body_work'")
    if not cursor.fetchone():
        cursor.execute('''
            CREATE TABLE body_work (
                body_work_id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER NOT NULL,
                date DATE NOT NULL,
                work_type TEXT CHECK(work_type IN (
                    'Denting', 'Painting', 'Bumper Repair', 'Windshield Replacement',
                    'Door Repair', 'Frame Straightening', 'Rust Removal', 'Full Body Paint', 'Touch Up', 'Ceramic Coating'
                )),
                cost DECIMAL(10,2),
                workshop_name TEXT,
                painter_name TEXT,
                color_code TEXT,
                panels_repaired TEXT,
                warranty_months INTEGER DEFAULT 6,
                notes TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("  - Body work table created")
    
    # ============================================
    # Create Tire Change table
    # ============================================
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tire_change'")
    if not cursor.fetchone():
        cursor.execute('''
            CREATE TABLE tire_change (
                tire_id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER NOT NULL,
                date DATE NOT NULL,
                tire_position TEXT CHECK(tire_position IN ('Front Left', 'Front Right', 'Rear Left', 'Rear Right', 'All Four', 'Spare')),
                tire_brand TEXT,
                tire_size TEXT,
                quantity INTEGER DEFAULT 1,
                cost_per_tire DECIMAL(10,2),
                total_cost DECIMAL(10,2),
                alignment_done INTEGER DEFAULT 0,
                balancing_done INTEGER DEFAULT 0,
                old_tire_condition TEXT,
                next_rotation_km INTEGER,
                workshop_name TEXT,
                notes TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("  - Tire change table created")
    
    # ============================================
    # Create Maintenance Schedule table
    # ============================================
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='maintenance_schedule'")
    if not cursor.fetchone():
        cursor.execute('''
            CREATE TABLE maintenance_schedule (
                schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER NOT NULL,
                maintenance_type TEXT NOT NULL,
                scheduled_date DATE,
                scheduled_km INTEGER,
                status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending', 'Completed', 'Overdue', 'Cancelled')),
                assigned_to INTEGER,
                completed_date DATE,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("  - Maintenance schedule table created")
    
    # ============================================
    # Create indexes
    # ============================================
    print("Creating indexes...")
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_maintenance_vehicle ON maintenance(vehicle_id)",
        "CREATE INDEX IF NOT EXISTS idx_maintenance_date ON maintenance(date)",
        "CREATE INDEX IF NOT EXISTS idx_maintenance_type ON maintenance(maintenance_type)",
        "CREATE INDEX IF NOT EXISTS idx_tuning_vehicle ON tuning(vehicle_id)",
        "CREATE INDEX IF NOT EXISTS idx_electrical_vehicle ON electrical_work(vehicle_id)",
        "CREATE INDEX IF NOT EXISTS idx_body_work_vehicle ON body_work(vehicle_id)",
        "CREATE INDEX IF NOT EXISTS idx_tire_vehicle ON tire_change(vehicle_id)",
        "CREATE INDEX IF NOT EXISTS idx_schedule_vehicle ON maintenance_schedule(vehicle_id)",
        "CREATE INDEX IF NOT EXISTS idx_schedule_status ON maintenance_schedule(status)"
    ]
    
    for index in indexes:
        try:
            cursor.execute(index)
        except Exception as e:
            print(f"  Warning: {e}")
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 50)
    print("Database upgrade completed successfully!")
    print("Added tables: tuning, electrical_work, body_work, tire_change, maintenance_schedule")
    print("Upgraded table: maintenance (added new columns)")
    print("=" * 50)

if __name__ == '__main__':
    upgrade_database()