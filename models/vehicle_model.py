from database.db_manager import get_db_connection
from datetime import datetime

class VehicleModel:
    
    @staticmethod
    def get_all_vehicles():
        """Get all vehicles with driver names"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT v.*, d.full_name as driver_name 
            FROM vehicles v
            LEFT JOIN drivers d ON v.assigned_driver_id = d.driver_id
            ORDER BY v.vehicle_id DESC
        ''')
        vehicles = cursor.fetchall()
        conn.close()
        return vehicles
    
    @staticmethod
    def get_vehicle_by_id(vehicle_id):
        """Get single vehicle by ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT v.*, d.full_name as driver_name, d.phone as driver_phone, d.license_no as driver_license
            FROM vehicles v
            LEFT JOIN drivers d ON v.assigned_driver_id = d.driver_id
            WHERE v.vehicle_id = ?
        ''', (vehicle_id,))
        vehicle = cursor.fetchone()
        conn.close()
        return vehicle
    
    @staticmethod
    def add_vehicle(data):
        """Add new vehicle"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if registration number already exists (a blank plate number is allowed)
        if data['registration_no']:
            cursor.execute("SELECT COUNT(*) FROM vehicles WHERE registration_no = ?", (data['registration_no'],))
            if cursor.fetchone()[0] > 0:
                conn.close()
                raise ValueError(f"Vehicle with registration {data['registration_no']} already exists!")

        cursor.execute('''
            INSERT INTO vehicles (
                registration_no, make, model, year, engine_no, chassis_no,
                purchase_date, purchase_cost, current_odometer, fuel_type, 
                status, assigned_driver_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            data['registration_no'], data['make'], data['model'], data['year'],
            data['engine_no'], data['chassis_no'], data['purchase_date'],
            data['purchase_cost'], data['current_odometer'], data['fuel_type'],
            data['status'], data['assigned_driver_id']
        ))
        conn.commit()
        vehicle_id = cursor.lastrowid
        conn.close()
        return vehicle_id
    
    @staticmethod
    def update_vehicle(vehicle_id, data):
        """Update vehicle information"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if registration number already exists for another vehicle (blank is allowed)
        if data['registration_no']:
            cursor.execute("SELECT COUNT(*) FROM vehicles WHERE registration_no = ? AND vehicle_id != ?",
                          (data['registration_no'], vehicle_id))
            if cursor.fetchone()[0] > 0:
                conn.close()
                raise ValueError(f"Vehicle with registration {data['registration_no']} already exists!")
        
        cursor.execute('''
            UPDATE vehicles SET
                registration_no=?, make=?, model=?, year=?, engine_no=?, chassis_no=?,
                purchase_date=?, purchase_cost=?, current_odometer=?, fuel_type=?,
                status=?, assigned_driver_id=?
            WHERE vehicle_id=?
        ''', (
            data['registration_no'], data['make'], data['model'], data['year'],
            data['engine_no'], data['chassis_no'], data['purchase_date'],
            data['purchase_cost'], data['current_odometer'], data['fuel_type'],
            data['status'], data['assigned_driver_id'], vehicle_id
        ))
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def delete_vehicle(vehicle_id):
        """Delete a vehicle"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # First unassign any drivers
        cursor.execute("UPDATE vehicles SET assigned_driver_id = NULL WHERE vehicle_id = ?", (vehicle_id,))
        cursor.execute("DELETE FROM vehicles WHERE vehicle_id = ?", (vehicle_id,))
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def update_odometer(vehicle_id, new_odometer):
        """Update vehicle odometer reading"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Only update if new odometer is greater than current
        cursor.execute('''
            UPDATE vehicles 
            SET current_odometer = ? 
            WHERE vehicle_id = ? AND current_odometer < ?
        ''', (new_odometer, vehicle_id, new_odometer))
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def assign_driver(vehicle_id, driver_id):
        """Assign a driver to a vehicle"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if driver already assigned to another vehicle
        cursor.execute("SELECT vehicle_id FROM vehicles WHERE assigned_driver_id = ?", (driver_id,))
        existing = cursor.fetchone()
        if existing:
            conn.close()
            raise ValueError("Driver is already assigned to another vehicle!")
        
        cursor.execute("UPDATE vehicles SET assigned_driver_id = ? WHERE vehicle_id = ?", 
                      (driver_id, vehicle_id))
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def unassign_driver(vehicle_id):
        """Unassign driver from vehicle"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE vehicles SET assigned_driver_id = NULL WHERE vehicle_id = ?", (vehicle_id,))
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def update_status(vehicle_id, status):
        """Update vehicle status"""
        valid_statuses = ['Active', 'Under Repair', 'Retired']
        if status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE vehicles SET status = ? WHERE vehicle_id = ?", (status, vehicle_id))
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def get_vehicle_stats():
        """Get vehicle statistics for dashboard"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Total vehicles
        cursor.execute("SELECT COUNT(*) FROM vehicles")
        stats['total_vehicles'] = cursor.fetchone()[0]
        
        # Active vehicles
        cursor.execute("SELECT COUNT(*) FROM vehicles WHERE status = 'Active'")
        stats['active_vehicles'] = cursor.fetchone()[0]
        
        # Vehicles under repair
        cursor.execute("SELECT COUNT(*) FROM vehicles WHERE status = 'Under Repair'")
        stats['under_repair'] = cursor.fetchone()[0]
        
        # Retired vehicles
        cursor.execute("SELECT COUNT(*) FROM vehicles WHERE status = 'Retired'")
        stats['retired_vehicles'] = cursor.fetchone()[0]
        
        # Total fuel consumption this month
        cursor.execute('''
            SELECT SUM(total_cost) FROM fuel_consumption 
            WHERE strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
            AND status = 'Approved'
        ''')
        result = cursor.fetchone()
        stats['monthly_fuel_cost'] = result[0] if result[0] else 0
        
        # Total maintenance cost this month
        cursor.execute('''
            SELECT SUM(cost) FROM maintenance 
            WHERE strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
        ''')
        result = cursor.fetchone()
        stats['monthly_maintenance_cost'] = result[0] if result[0] else 0
        
        # Total vehicles with low fuel efficiency
        cursor.execute('''
            SELECT COUNT(DISTINCT vehicle_id) FROM fuel_consumption 
            WHERE status = 'Approved'
            GROUP BY vehicle_id
            HAVING (MAX(odometer_reading) - MIN(odometer_reading)) / SUM(liters) < 8
        ''')
        stats['low_efficiency_vehicles'] = len(cursor.fetchall())
        
        conn.close()
        return stats
    
    @staticmethod
    def get_available_vehicles():
        """Get vehicles that are active and not assigned"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM vehicles 
            WHERE status = 'Active' AND assigned_driver_id IS NULL
            ORDER BY make, model
        ''')
        
        vehicles = cursor.fetchall()
        conn.close()
        return vehicles
    
    @staticmethod
    def get_vehicle_by_driver(driver_id):
        """Get vehicle assigned to a driver"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM vehicles WHERE assigned_driver_id = ?
        ''', (driver_id,))
        
        vehicle = cursor.fetchone()
        conn.close()
        return vehicle
    
    @staticmethod
    def search_vehicles(query):
        """Search vehicles by registration, make, or model"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        search_term = f"%{query}%"
        cursor.execute('''
            SELECT v.*, d.full_name as driver_name 
            FROM vehicles v
            LEFT JOIN drivers d ON v.assigned_driver_id = d.driver_id
            WHERE v.registration_no LIKE ? 
               OR v.make LIKE ? 
               OR v.model LIKE ?
            ORDER BY v.vehicle_id DESC
        ''', (search_term, search_term, search_term))
        
        vehicles = cursor.fetchall()
        conn.close()
        return vehicles
    
    @staticmethod
    def get_vehicles_by_status(status):
        """Get vehicles filtered by status"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT v.*, d.full_name as driver_name 
            FROM vehicles v
            LEFT JOIN drivers d ON v.assigned_driver_id = d.driver_id
            WHERE v.status = ?
            ORDER BY v.vehicle_id DESC
        ''', (status,))
        
        vehicles = cursor.fetchall()
        conn.close()
        return vehicles
    
    @staticmethod
    def get_vehicle_maintenance_summary(vehicle_id):
        """Get maintenance summary for a specific vehicle"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        summary = {}
        
        # Last oil change
        cursor.execute('''
            SELECT * FROM maintenance 
            WHERE vehicle_id = ? AND type = 'Oil Change'
            ORDER BY date DESC LIMIT 1
        ''', (vehicle_id,))
        summary['last_oil_change'] = cursor.fetchone()
        
        # Last air filter change
        cursor.execute('''
            SELECT * FROM maintenance 
            WHERE vehicle_id = ? AND type = 'Air Filter'
            ORDER BY date DESC LIMIT 1
        ''', (vehicle_id,))
        summary['last_air_filter'] = cursor.fetchone()
        
        # Last oil filter change
        cursor.execute('''
            SELECT * FROM maintenance 
            WHERE vehicle_id = ? AND type = 'Oil Filter'
            ORDER BY date DESC LIMIT 1
        ''', (vehicle_id,))
        summary['last_oil_filter'] = cursor.fetchone()
        
        # Total maintenance cost
        cursor.execute('''
            SELECT SUM(cost) as total FROM maintenance WHERE vehicle_id = ?
        ''', (vehicle_id,))
        result = cursor.fetchone()
        summary['total_maintenance_cost'] = result['total'] if result['total'] else 0
        
        conn.close()
        return summary
    
    @staticmethod
    def get_vehicle_fuel_summary(vehicle_id):
        """Get fuel summary for a specific vehicle"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        summary = {}
        
        # Total fuel consumed
        cursor.execute('''
            SELECT SUM(liters) as total_liters, SUM(total_cost) as total_cost
            FROM fuel_consumption 
            WHERE vehicle_id = ? AND status = 'Approved'
        ''', (vehicle_id,))
        result = cursor.fetchone()
        summary['total_liters'] = result['total_liters'] if result['total_liters'] else 0
        summary['total_fuel_cost'] = result['total_cost'] if result['total_cost'] else 0
        
        # Average fuel efficiency
        cursor.execute('''
            SELECT 
                (MAX(odometer_reading) - MIN(odometer_reading)) as km_driven,
                SUM(liters) as total_liters
            FROM fuel_consumption 
            WHERE vehicle_id = ? AND status = 'Approved'
        ''', (vehicle_id,))
        result = cursor.fetchone()
        
        if result['total_liters'] and result['total_liters'] > 0 and result['km_driven']:
            summary['avg_efficiency'] = round(result['km_driven'] / result['total_liters'], 2)
        else:
            summary['avg_efficiency'] = 0
        
        conn.close()
        return summary
    
    @staticmethod
    def get_vehicle_count_by_fuel_type():
        """Get vehicle count grouped by fuel type"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT fuel_type, COUNT(*) as count 
            FROM vehicles 
            GROUP BY fuel_type
        ''')
        
        results = cursor.fetchall()
        conn.close()
        return results
    
    @staticmethod
    def get_vehicle_count_by_status():
        """Get vehicle count grouped by status"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT status, COUNT(*) as count 
            FROM vehicles 
            GROUP BY status
        ''')
        
        results = cursor.fetchall()
        conn.close()
        return results