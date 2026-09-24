from database.db_manager import get_db_connection
from datetime import datetime, timedelta

class FuelModel:
    
    @staticmethod
    def add_fuel_entry(data):
        """Add fuel consumption entry"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        total_cost = data['liters'] * data['cost_per_liter']
        
        cursor.execute('''
            INSERT INTO fuel_consumption 
            (vehicle_id, date, liters, cost_per_liter, total_cost, odometer_reading, 
             fuel_station, receipt_image, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['vehicle_id'], data['date'], data['liters'], data['cost_per_liter'],
            total_cost, data['odometer_reading'], data.get('fuel_station', ''),
            data.get('receipt_image', ''), data.get('status', 'Pending')
        ))
        
        conn.commit()
        fuel_id = cursor.lastrowid
        
        # Update vehicle odometer
        cursor.execute('''
            UPDATE vehicles SET current_odometer = ? 
            WHERE vehicle_id = ? AND current_odometer < ?
        ''', (data['odometer_reading'], data['vehicle_id'], data['odometer_reading']))
        
        conn.commit()
        conn.close()
        return fuel_id
    
    @staticmethod
    def get_fuel_entries(vehicle_id=None, start_date=None, end_date=None, limit=None, status=None):
        """Get fuel entries with filters"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT f.*, v.registration_no, v.make, v.model, v.fuel_type
            FROM fuel_consumption f
            LEFT JOIN vehicles v ON f.vehicle_id = v.vehicle_id
            WHERE 1=1
        '''
        params = []
        
        if vehicle_id:
            query += " AND f.vehicle_id = ?"
            params.append(vehicle_id)
        if start_date:
            query += " AND f.date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND f.date <= ?"
            params.append(end_date)
        if status:
            query += " AND f.status = ?"
            params.append(status)
        
        query += " ORDER BY f.date DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        cursor.execute(query, params)
        entries = cursor.fetchall()
        conn.close()
        return entries
    
    @staticmethod
    def get_fuel_entry_by_id(fuel_id):
        """Get single fuel entry by ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT f.*, v.registration_no, v.make, v.model
            FROM fuel_consumption f
            LEFT JOIN vehicles v ON f.vehicle_id = v.vehicle_id
            WHERE f.fuel_id = ?
        ''', (fuel_id,))
        
        entry = cursor.fetchone()
        conn.close()
        return entry
    
    @staticmethod
    def get_fuel_efficiency(vehicle_id, days=30):
        """Calculate fuel efficiency (km per liter) for last N days"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get entries in date range
        date_threshold = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        cursor.execute('''
            SELECT 
                MIN(odometer_reading) as start_km,
                MAX(odometer_reading) as end_km,
                SUM(liters) as total_liters
            FROM fuel_consumption
            WHERE vehicle_id = ? 
            AND date >= ?
            AND status = 'Approved'
        ''', (vehicle_id, date_threshold))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result['total_liters'] and result['total_liters'] > 0:
            km_driven = (result['end_km'] or 0) - (result['start_km'] or 0)
            if km_driven > 0:
                efficiency = km_driven / result['total_liters']
                return round(efficiency, 2)
        return 0
    
    @staticmethod
    def get_fuel_efficiency_by_period(vehicle_id, start_date, end_date):
        """Calculate fuel efficiency for specific period"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                MIN(odometer_reading) as start_km,
                MAX(odometer_reading) as end_km,
                SUM(liters) as total_liters
            FROM fuel_consumption
            WHERE vehicle_id = ? 
            AND date BETWEEN ? AND ?
            AND status = 'Approved'
        ''', (vehicle_id, start_date, end_date))
        
        result = cursor.fetchone()
        conn.close()
        
        if result and result['total_liters'] and result['total_liters'] > 0:
            km_driven = (result['end_km'] or 0) - (result['start_km'] or 0)
            if km_driven > 0:
                efficiency = km_driven / result['total_liters']
                return round(efficiency, 2)
        return 0
    
    @staticmethod
    def approve_fuel_entry(fuel_id, approved_by):
        """Approve a fuel entry"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE fuel_consumption SET status = 'Approved', approved_by = ?
            WHERE fuel_id = ?
        ''', (approved_by, fuel_id))
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def reject_fuel_entry(fuel_id, reason=None):
        """Reject a fuel entry"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE fuel_consumption SET status = 'Rejected'
            WHERE fuel_id = ?
        ''', (fuel_id,))
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def update_fuel_entry(fuel_id, data):
        """Update a fuel entry"""
        conn = get_db_connection()
        cursor = conn.cursor()
        total_cost = data['liters'] * data['cost_per_liter']
        cursor.execute('''
            UPDATE fuel_consumption
            SET vehicle_id = ?, date = ?, liters = ?, cost_per_liter = ?,
                total_cost = ?, odometer_reading = ?, fuel_station = ?
            WHERE fuel_id = ?
        ''', (
            data['vehicle_id'], data['date'], data['liters'], data['cost_per_liter'],
            total_cost, data['odometer_reading'], data.get('fuel_station', ''), fuel_id
        ))
        # Update vehicle odometer if higher
        cursor.execute('''
            UPDATE vehicles SET current_odometer = ? 
            WHERE vehicle_id = ? AND current_odometer < ?
        ''', (data['odometer_reading'], data['vehicle_id'], data['odometer_reading']))
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def delete_fuel_entry(fuel_id):
        """Delete a fuel entry"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM fuel_consumption WHERE fuel_id = ?", (fuel_id,))
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def get_monthly_cost(vehicle_id, month):
        """Get fuel cost for a specific month (format: YYYY-MM)"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT SUM(total_cost) as total FROM fuel_consumption 
            WHERE vehicle_id = ? 
            AND strftime('%Y-%m', date) = ?
            AND status = 'Approved'
        ''', (vehicle_id, month))
        
        result = cursor.fetchone()
        conn.close()
        return result['total'] if result['total'] else 0
    
    @staticmethod
    def get_total_fuel_cost(vehicle_id=None, start_date=None, end_date=None):
        """Get total fuel cost with filters"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT SUM(total_cost) as total FROM fuel_consumption WHERE status = 'Approved'"
        params = []
        
        if vehicle_id:
            query += " AND vehicle_id = ?"
            params.append(vehicle_id)
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        
        cursor.execute(query, params)
        result = cursor.fetchone()
        conn.close()
        return result['total'] if result['total'] else 0
    
    @staticmethod
    def get_total_liters(vehicle_id=None, start_date=None, end_date=None):
        """Get total liters consumed with filters"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT SUM(liters) as total FROM fuel_consumption WHERE status = 'Approved'"
        params = []
        
        if vehicle_id:
            query += " AND vehicle_id = ?"
            params.append(vehicle_id)
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        
        cursor.execute(query, params)
        result = cursor.fetchone()
        conn.close()
        return result['total'] if result['total'] else 0
    
    @staticmethod
    def get_fuel_summary_by_vehicle(month=None):
        """Get fuel summary grouped by vehicle"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT 
                v.vehicle_id,
                v.registration_no,
                v.make,
                v.model,
                COUNT(f.fuel_id) as fillups,
                SUM(f.liters) as total_liters,
                SUM(f.total_cost) as total_cost,
                AVG(f.liters) as avg_liters_per_fillup
            FROM vehicles v
            LEFT JOIN fuel_consumption f ON v.vehicle_id = f.vehicle_id AND f.status = 'Approved'
        '''
        
        if month:
            query += f" AND strftime('%Y-%m', f.date) = '{month}'"
        
        query += " GROUP BY v.vehicle_id ORDER BY total_cost DESC"
        
        cursor.execute(query)
        summary = cursor.fetchall()
        conn.close()
        return summary
    
    @staticmethod
    def get_daily_fuel_consumption(vehicle_id, days=7):
        """Get daily fuel consumption for last N days"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        date_threshold = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        cursor.execute('''
            SELECT 
                date,
                SUM(liters) as daily_liters,
                SUM(total_cost) as daily_cost
            FROM fuel_consumption
            WHERE vehicle_id = ? 
            AND date >= ?
            AND status = 'Approved'
            GROUP BY date
            ORDER BY date DESC
        ''', (vehicle_id, date_threshold))
        
        consumption = cursor.fetchall()
        conn.close()
        return consumption
    
    @staticmethod
    def get_pending_approvals():
        """Get all pending fuel entries for approval"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT f.*, v.registration_no, v.make, v.model
            FROM fuel_consumption f
            LEFT JOIN vehicles v ON f.vehicle_id = v.vehicle_id
            WHERE f.status = 'Pending'
            ORDER BY f.date DESC
        ''')
        
        pending = cursor.fetchall()
        conn.close()
        return pending
    
    @staticmethod
    def get_last_fuel_entry(vehicle_id):
        """Get last fuel entry for a vehicle"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM fuel_consumption 
            WHERE vehicle_id = ? AND status = 'Approved'
            ORDER BY date DESC LIMIT 1
        ''', (vehicle_id,))
        
        entry = cursor.fetchone()
        conn.close()
        return entry
    
    @staticmethod
    def get_fuel_cost_by_month(vehicle_id=None, year=None):
        """Get fuel cost grouped by month"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT 
                strftime('%Y-%m', date) as month,
                SUM(total_cost) as total_cost,
                SUM(liters) as total_liters
            FROM fuel_consumption
            WHERE status = 'Approved'
        '''
        params = []
        
        if vehicle_id:
            query += " AND vehicle_id = ?"
            params.append(vehicle_id)
        if year:
            query += " AND strftime('%Y', date) = ?"
            params.append(str(year))
        
        query += " GROUP BY strftime('%Y-%m', date) ORDER BY month DESC"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        return results