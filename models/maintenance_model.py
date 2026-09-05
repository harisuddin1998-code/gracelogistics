from database.db_manager import get_db_connection
from datetime import datetime

class MaintenanceModel:
    
    # ============================================
    # OIL CHANGE METHODS
    # ============================================
    
    @staticmethod
    def add_oil_change(data):
        """Add oil change record"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO maintenance (vehicle_id, maintenance_type, date, cost, quantity, unit_price, 
                                   next_due_km, next_due_date, mechanic_name, notes, created_by)
            VALUES (?, 'Oil Change', ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['vehicle_id'], data['date'], data['cost'], data.get('quantity', 1),
            data.get('unit_price', data['cost']), data.get('next_due_km'), 
            data.get('next_due_date'), data.get('mechanic_name'), data.get('notes', ''),
            data.get('created_by', 1)
        ))
        conn.commit()
        maintenance_id = cursor.lastrowid
        conn.close()
        return maintenance_id
    
    @staticmethod
    def get_oil_change_history(vehicle_id=None, start_date=None, end_date=None):
        """Get oil change history"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT m.*, v.registration_no, v.make, v.model, v.current_odometer
            FROM maintenance m
            JOIN vehicles v ON m.vehicle_id = v.vehicle_id
            WHERE m.maintenance_type = 'Oil Change'
        '''
        params = []
        
        if vehicle_id:
            query += " AND m.vehicle_id = ?"
            params.append(vehicle_id)
        if start_date:
            query += " AND m.date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND m.date <= ?"
            params.append(end_date)
        
        query += " ORDER BY m.date DESC"
        
        cursor.execute(query, params)
        records = cursor.fetchall()
        conn.close()
        return records
    
    # ============================================
    # FILTER CHANGE METHODS
    # ============================================
    
    @staticmethod
    def add_filter_change(data, filter_type):
        """Add filter change record"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO maintenance (vehicle_id, maintenance_type, date, cost, quantity, unit_price, 
                                   next_due_km, next_due_date, mechanic_name, notes, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['vehicle_id'], filter_type, data['date'], data['cost'], data.get('quantity', 1),
            data.get('unit_price', data['cost']), data.get('next_due_km'), 
            data.get('next_due_date'), data.get('mechanic_name'), data.get('notes', ''),
            data.get('created_by', 1)
        ))
        conn.commit()
        maintenance_id = cursor.lastrowid
        conn.close()
        return maintenance_id
    
    @staticmethod
    def get_filter_history(vehicle_id=None, filter_type=None):
        """Get filter change history"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT m.*, v.registration_no, v.make, v.model
            FROM maintenance m
            JOIN vehicles v ON m.vehicle_id = v.vehicle_id
            WHERE m.maintenance_type IN ('Air Filter', 'Oil Filter', 'Fuel Filter', 'Cabin Filter')
        '''
        params = []
        
        if vehicle_id:
            query += " AND m.vehicle_id = ?"
            params.append(vehicle_id)
        if filter_type:
            query += " AND m.maintenance_type = ?"
            params.append(filter_type)
        
        query += " ORDER BY m.date DESC"
        
        cursor.execute(query, params)
        records = cursor.fetchall()
        conn.close()
        return records
    
    # ============================================
    # TUNING METHODS
    # ============================================
    
    @staticmethod
    def add_tuning(data):
        """Add tuning record"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tuning (vehicle_id, date, tuning_type, cost, technician_name, 
                               before_performance, after_performance, notes, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['vehicle_id'], data['date'], data['tuning_type'], data['cost'],
            data.get('technician_name'), data.get('before_performance', ''),
            data.get('after_performance', ''), data.get('notes', ''),
            data.get('created_by', 1)
        ))
        conn.commit()
        tuning_id = cursor.lastrowid
        conn.close()
        return tuning_id
    
    @staticmethod
    def get_tuning_history(vehicle_id=None):
        """Get tuning history"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT t.*, v.registration_no, v.make, v.model
            FROM tuning t
            JOIN vehicles v ON t.vehicle_id = v.vehicle_id
            WHERE 1=1
        '''
        params = []
        
        if vehicle_id:
            query += " AND t.vehicle_id = ?"
            params.append(vehicle_id)
        
        query += " ORDER BY t.date DESC"
        
        cursor.execute(query, params)
        records = cursor.fetchall()
        conn.close()
        return records
    
    # ============================================
    # ELECTRICAL WORK METHODS
    # ============================================
    
    @staticmethod
    def add_electrical_work(data):
        """Add electrical work record"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO electrical_work (vehicle_id, date, work_type, cost, technician_name, 
                                        parts_used, hours_spent, notes, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['vehicle_id'], data['date'], data['work_type'], data['cost'],
            data.get('technician_name'), data.get('parts_used', ''),
            data.get('hours_spent', 0), data.get('notes', ''),
            data.get('created_by', 1)
        ))
        conn.commit()
        electrical_id = cursor.lastrowid
        conn.close()
        return electrical_id
    
    @staticmethod
    def get_electrical_history(vehicle_id=None):
        """Get electrical work history"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT e.*, v.registration_no, v.make, v.model
            FROM electrical_work e
            JOIN vehicles v ON e.vehicle_id = v.vehicle_id
            WHERE 1=1
        '''
        params = []
        
        if vehicle_id:
            query += " AND e.vehicle_id = ?"
            params.append(vehicle_id)
        
        query += " ORDER BY e.date DESC"
        
        cursor.execute(query, params)
        records = cursor.fetchall()
        conn.close()
        return records
    
    # ============================================
    # BODY WORK METHODS
    # ============================================
    
    @staticmethod
    def add_body_work(data):
        """Add body work record"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO body_work (vehicle_id, date, work_type, cost, workshop_name, 
                                  painter_name, color_code, panels_repaired, warranty_months, notes, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['vehicle_id'], data['date'], data['work_type'], data['cost'],
            data.get('workshop_name'), data.get('painter_name'), data.get('color_code', ''),
            data.get('panels_repaired', ''), data.get('warranty_months', 6), data.get('notes', ''),
            data.get('created_by', 1)
        ))
        conn.commit()
        body_work_id = cursor.lastrowid
        conn.close()
        return body_work_id
    
    @staticmethod
    def get_body_work_history(vehicle_id=None):
        """Get body work history"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT b.*, v.registration_no, v.make, v.model
            FROM body_work b
            JOIN vehicles v ON b.vehicle_id = v.vehicle_id
            WHERE 1=1
        '''
        params = []
        
        if vehicle_id:
            query += " AND b.vehicle_id = ?"
            params.append(vehicle_id)
        
        query += " ORDER BY b.date DESC"
        
        cursor.execute(query, params)
        records = cursor.fetchall()
        conn.close()
        return records
    
    # ============================================
    # TIRE CHANGE METHODS
    # ============================================
    
    @staticmethod
    def add_tire_change(data):
        """Add tire change record"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        total_cost = data['cost_per_tire'] * data['quantity']
        
        cursor.execute('''
            INSERT INTO tire_change (vehicle_id, date, tire_position, tire_brand, tire_size, 
                                    quantity, cost_per_tire, total_cost, alignment_done, 
                                    balancing_done, old_tire_condition, next_rotation_km, workshop_name, notes, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['vehicle_id'], data['date'], data['tire_position'], data.get('tire_brand', ''),
            data.get('tire_size', ''), data['quantity'], data['cost_per_tire'], total_cost,
            1 if data.get('alignment_done') else 0, 1 if data.get('balancing_done') else 0,
            data.get('old_tire_condition', ''), data.get('next_rotation_km', 0),
            data.get('workshop_name', ''), data.get('notes', ''),
            data.get('created_by', 1)
        ))
        conn.commit()
        tire_id = cursor.lastrowid
        conn.close()
        return tire_id
    
    @staticmethod
    def get_tire_history(vehicle_id=None):
        """Get tire change history"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT t.*, v.registration_no, v.make, v.model
            FROM tire_change t
            JOIN vehicles v ON t.vehicle_id = v.vehicle_id
            WHERE 1=1
        '''
        params = []
        
        if vehicle_id:
            query += " AND t.vehicle_id = ?"
            params.append(vehicle_id)
        
        query += " ORDER BY t.date DESC"
        
        cursor.execute(query, params)
        records = cursor.fetchall()
        conn.close()
        return records
    
    # ============================================
    # SCHEDULE METHODS
    # ============================================
    
    @staticmethod
    def add_schedule(data):
        """Add maintenance schedule"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO maintenance_schedule (vehicle_id, maintenance_type, scheduled_date, scheduled_km, status, assigned_to, notes)
            VALUES (?, ?, ?, ?, 'Pending', ?, ?)
        ''', (
            data['vehicle_id'], data['maintenance_type'], data.get('scheduled_date'),
            data.get('scheduled_km', 0), data.get('assigned_to'), data.get('notes', '')
        ))
        conn.commit()
        schedule_id = cursor.lastrowid
        conn.close()
        return schedule_id
    
    @staticmethod
    def get_schedules(vehicle_id=None, status=None):
        """Get maintenance schedules"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT s.*, v.registration_no, v.make, v.model
            FROM maintenance_schedule s
            JOIN vehicles v ON s.vehicle_id = v.vehicle_id
            WHERE 1=1
        '''
        params = []
        
        if vehicle_id:
            query += " AND s.vehicle_id = ?"
            params.append(vehicle_id)
        if status:
            query += " AND s.status = ?"
            params.append(status)
        
        query += " ORDER BY s.scheduled_date ASC, s.scheduled_km ASC"
        
        cursor.execute(query, params)
        records = cursor.fetchall()
        conn.close()
        return records
    
    @staticmethod
    def update_schedule_status(schedule_id, status, completed_date=None):
        """Update schedule status"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if completed_date:
            cursor.execute('''
                UPDATE maintenance_schedule 
                SET status = ?, completed_date = ?
                WHERE schedule_id = ?
            ''', (status, completed_date, schedule_id))
        else:
            cursor.execute('''
                UPDATE maintenance_schedule SET status = ? WHERE schedule_id = ?
            ''', (status, schedule_id))
        
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def delete_schedule(schedule_id):
        """Delete a schedule"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM maintenance_schedule WHERE schedule_id = ?", (schedule_id,))
        conn.commit()
        conn.close()
        return True
    
    # ============================================
    # REPORT METHODS
    # ============================================
    
    @staticmethod
    def get_maintenance_summary(vehicle_id=None, start_date=None, end_date=None):
        """Get maintenance cost summary by type"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT 
                maintenance_type,
                COUNT(*) as total_count,
                SUM(cost) as total_cost,
                AVG(cost) as avg_cost,
                MIN(date) as first_date,
                MAX(date) as last_date
            FROM maintenance
            WHERE 1=1
        '''
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
        
        query += " GROUP BY maintenance_type ORDER BY total_cost DESC"
        
        cursor.execute(query, params)
        summary = cursor.fetchall()
        conn.close()
        return summary
    
    @staticmethod
    def get_total_maintenance_cost(vehicle_id=None):
        """Get total maintenance cost"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT SUM(cost) as total FROM maintenance WHERE 1=1"
        params = []
        
        if vehicle_id:
            query += " AND vehicle_id = ?"
            params.append(vehicle_id)
        
        cursor.execute(query, params)
        result = cursor.fetchone()
        conn.close()
        return result['total'] if result['total'] else 0