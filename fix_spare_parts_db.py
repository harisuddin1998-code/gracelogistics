import sqlite3
import os

def fix_spare_parts_database():
    db_path = 'instance/vehicle_management.db'
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("FIXING SPARE PARTS DATABASE")
    print("=" * 60)
    
    # Check and create spare_parts_inventory table if not exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spare_parts_inventory'")
    if not cursor.fetchone():
        print("Creating spare_parts_inventory table...")
        cursor.execute('''
            CREATE TABLE spare_parts_inventory (
                part_id INTEGER PRIMARY KEY AUTOINCREMENT,
                part_name TEXT NOT NULL,
                part_number TEXT UNIQUE,
                category TEXT,
                quantity_in_stock INTEGER DEFAULT 0,
                reorder_level INTEGER DEFAULT 5,
                unit_cost DECIMAL(10,2),
                selling_price DECIMAL(10,2),
                location TEXT,
                supplier_name TEXT,
                last_ordered_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("  - spare_parts_inventory table created")
    else:
        print("✓ spare_parts_inventory table exists")
    
    # Check and create spare_parts_expense table
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='spare_parts_expense'")
    if not cursor.fetchone():
        print("Creating spare_parts_expense table...")
        cursor.execute('''
            CREATE TABLE spare_parts_expense (
                expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER NOT NULL,
                part_id INTEGER NOT NULL,
                vendor_id INTEGER,
                date DATE NOT NULL,
                quantity_used INTEGER NOT NULL,
                unit_price DECIMAL(10,2),
                total_cost DECIMAL(10,2),
                mechanic_name TEXT,
                failure_reason TEXT,
                warranty_until DATE,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id),
                FOREIGN KEY (part_id) REFERENCES spare_parts_inventory(part_id)
            )
        ''')
        print("  - spare_parts_expense table created")
    else:
        print("✓ spare_parts_expense table exists")
    
    # Insert sample spare parts if empty
    cursor.execute("SELECT COUNT(*) FROM spare_parts_inventory")
    if cursor.fetchone()[0] == 0:
        print("Inserting sample spare parts...")
        sample_parts = [
            ('Engine Oil 5W30', 'OIL001', 'Fluids', 20, 5, 2500, 3000, 'Shelf A1', 'AutoParts Co.', '2024-01-15'),
            ('Air Filter', 'AF001', 'Filters', 15, 3, 800, 1000, 'Shelf B2', 'FilterMaster', '2024-01-20'),
            ('Oil Filter', 'OF001', 'Filters', 18, 4, 600, 800, 'Shelf B3', 'FilterMaster', '2024-01-20'),
            ('Brake Pads Front', 'BP001', 'Brakes', 10, 2, 3500, 4200, 'Shelf C1', 'SafetyBrake', '2024-02-01'),
            ('Brake Pads Rear', 'BP002', 'Brakes', 8, 2, 3200, 3900, 'Shelf C2', 'SafetyBrake', '2024-02-01'),
            ('Spark Plug', 'SP001', 'Engine', 25, 5, 400, 550, 'Shelf A3', 'EnginePro', '2024-02-10'),
            ('Timing Belt', 'TB001', 'Engine', 5, 2, 2800, 3500, 'Shelf A4', 'EnginePro', '2024-02-15'),
            ('Battery 12V', 'BT001', 'Electrical', 6, 2, 5500, 7000, 'Shelf D1', 'AutoParts Co.', '2024-03-01'),
            ('Coolant 5L', 'CL001', 'Fluids', 15, 3, 1200, 1600, 'Shelf A5', 'AutoParts Co.', '2024-03-10'),
            ('Tire 185/65R14', 'TR001', 'Tires', 12, 4, 8500, 10500, 'Shelf E1', 'TireWorld', '2024-03-15')
        ]
        
        for part in sample_parts:
            cursor.execute('''
                INSERT INTO spare_parts_inventory 
                (part_name, part_number, category, quantity_in_stock, reorder_level, 
                 unit_cost, selling_price, location, supplier_name, last_ordered_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', part)
        print(f"  - {len(sample_parts)} sample parts inserted")
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 60)
    print("DATABASE FIX COMPLETED!")
    print("=" * 60)
    print("\nYou can now use the Spare Parts module.")
    print("Run: python app.py")

if __name__ == '__main__':
    fix_spare_parts_database()