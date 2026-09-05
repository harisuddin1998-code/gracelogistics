from database.db_manager import get_db_connection
from datetime import datetime

class DriverModel:
    
    @staticmethod
    def get_all_drivers():
        """Get all drivers"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT d.*, 
                   v.registration_no as assigned_vehicle,
                   (SELECT COUNT(*) FROM vehicles WHERE assigned_driver_id = d.driver_id) as vehicle_count
            FROM drivers d
            LEFT JOIN vehicles v ON d.driver_id = v.assigned_driver_id
            ORDER BY d.driver_id
        ''')
        drivers = cursor.fetchall()
        conn.close()
        return drivers
    
    @staticmethod
    def get_driver_by_id(driver_id):
        """Get single driver by ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT d.*, v.registration_no as assigned_vehicle
            FROM drivers d
            LEFT JOIN vehicles v ON d.driver_id = v.assigned_driver_id
            WHERE d.driver_id = ?
        ''', (driver_id,))
        driver = cursor.fetchone()
        conn.close()
        return driver
    
    @staticmethod
    def add_driver(data):
        """Add new driver"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO drivers (full_name, license_no, phone, address, joining_date, 
                               base_salary, advance_balance, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['full_name'], data['license_no'], data['phone'], data['address'],
            data['joining_date'], data['base_salary'], data.get('advance_balance', 0),
            data.get('status', 'Active')
        ))
        conn.commit()
        driver_id = cursor.lastrowid
        conn.close()
        return driver_id
    
    @staticmethod
    def update_driver(driver_id, data):
        """Update driver information"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE drivers SET
            full_name=?, license_no=?, phone=?, address=?, joining_date=?,
            base_salary=?, status=?
            WHERE driver_id=?
        ''', (
            data['full_name'], data['license_no'], data['phone'], data['address'],
            data['joining_date'], data['base_salary'], data['status'], driver_id
        ))
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def update_advance_balance(driver_id, amount, operation='add'):
        """Update driver's advance balance"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT advance_balance FROM drivers WHERE driver_id = ?", (driver_id,))
        current = cursor.fetchone()
        
        if operation == 'add':
            new_balance = current['advance_balance'] + amount
        else:  # deduct
            new_balance = current['advance_balance'] - amount
        
        cursor.execute("UPDATE drivers SET advance_balance = ? WHERE driver_id = ?", 
                      (new_balance, driver_id))
        conn.commit()
        conn.close()
        return new_balance
    
    @staticmethod
    def get_driver_stats():
        """Get driver statistics"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        stats = {}
        cursor.execute("SELECT COUNT(*) FROM drivers WHERE status = 'Active'")
        stats['active_drivers'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM drivers WHERE status = 'Inactive'")
        stats['inactive_drivers'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(advance_balance) FROM drivers")
        result = cursor.fetchone()
        stats['total_advances'] = result[0] if result[0] else 0
        
        cursor.execute("SELECT AVG(base_salary) FROM drivers WHERE status = 'Active'")
        result = cursor.fetchone()
        stats['avg_salary'] = result[0] if result[0] else 0
        
        cursor.execute("SELECT SUM(base_salary) FROM drivers WHERE status = 'Active'")
        result = cursor.fetchone()
        stats['total_monthly_salary'] = result[0] if result[0] else 0
        
        conn.close()
        return stats
    
    @staticmethod
    def delete_driver(driver_id):
        """Delete a driver"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # First unassign any vehicles
        cursor.execute("UPDATE vehicles SET assigned_driver_id = NULL WHERE assigned_driver_id = ?", (driver_id,))
        
        cursor.execute("DELETE FROM drivers WHERE driver_id = ?", (driver_id,))
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def get_drivers_with_advance():
        """Get drivers who have pending advances"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM drivers 
            WHERE advance_balance > 0
            ORDER BY advance_balance DESC
        ''')
        
        drivers = cursor.fetchall()
        conn.close()
        return drivers