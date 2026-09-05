from database.db_manager import get_db_connection
from datetime import datetime

class AdvanceModel:
    
    @staticmethod
    def add_advance(data):
        """Add advance salary record"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO driver_advances (driver_id, date, amount, reason, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (data['driver_id'], data['date'], data['amount'], 
              data['reason'], data.get('status', 'Pending')))
        
        conn.commit()
        advance_id = cursor.lastrowid
        conn.close()
        return advance_id
    
    @staticmethod
    def get_all_advances():
        """Get all advance records"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT a.*, d.full_name, d.base_salary, d.phone, d.license_no
            FROM driver_advances a
            JOIN drivers d ON a.driver_id = d.driver_id
            ORDER BY a.date DESC
        ''')
        
        advances = cursor.fetchall()
        conn.close()
        return advances
    
    @staticmethod
    def get_pending_advances():
        """Get all pending advances"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT a.*, d.full_name, d.base_salary, d.phone, d.license_no
            FROM driver_advances a
            JOIN drivers d ON a.driver_id = d.driver_id
            WHERE a.status = 'Pending'
            ORDER BY a.date DESC
        ''')
        
        advances = cursor.fetchall()
        conn.close()
        return advances
    
    @staticmethod
    def get_advances_by_driver(driver_id):
        """Get advances for specific driver"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM driver_advances 
            WHERE driver_id = ?
            ORDER BY date DESC
        ''', (driver_id,))
        
        advances = cursor.fetchall()
        conn.close()
        return advances
    
    @staticmethod
    def get_advance_by_id(advance_id):
        """Get single advance record by ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT a.*, d.full_name, d.base_salary, d.phone, d.license_no
            FROM driver_advances a
            JOIN drivers d ON a.driver_id = d.driver_id
            WHERE a.advance_id = ?
        ''', (advance_id,))
        
        advance = cursor.fetchone()
        conn.close()
        return advance
    
    @staticmethod
    def update_advance(advance_id, data):
        """Update advance record"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE driver_advances 
            SET amount = ?, reason = ?, date = ?
            WHERE advance_id = ?
        ''', (data['amount'], data['reason'], data['date'], advance_id))
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def mark_deducted(advance_id, month):
        """Mark advance as deducted from salary"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE driver_advances 
            SET status = 'Deducted', deduction_month = ?
            WHERE advance_id = ?
        ''', (month, advance_id))
        
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def mark_paid_back(advance_id):
        """Mark advance as paid back (without salary deduction)"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE driver_advances 
            SET status = 'Paid Back'
            WHERE advance_id = ?
        ''', (advance_id,))
        
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def get_total_pending_amount():
        """Get total pending advance amount"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT SUM(amount) as total FROM driver_advances 
            WHERE status = 'Pending'
        ''')
        
        result = cursor.fetchone()
        conn.close()
        return result['total'] if result['total'] else 0
    
    @staticmethod
    def get_total_pending_by_driver(driver_id):
        """Get total pending amount for specific driver"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT SUM(amount) as total FROM driver_advances 
            WHERE driver_id = ? AND status = 'Pending'
        ''', (driver_id,))
        
        result = cursor.fetchone()
        conn.close()
        return result['total'] if result['total'] else 0
    
    @staticmethod
    def delete_advance(advance_id):
        """Delete an advance record"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get the amount, driver_id, and status before deleting
        cursor.execute("SELECT driver_id, amount, status FROM driver_advances WHERE advance_id = ?", (advance_id,))
        advance = cursor.fetchone()
        
        if advance and advance['status'] == 'Pending':
            # Update driver's advance balance only if it was still pending
            cursor.execute("UPDATE drivers SET advance_balance = MAX(0, advance_balance - ?) WHERE driver_id = ?",
                          (advance['amount'], advance['driver_id']))
        
        cursor.execute("DELETE FROM driver_advances WHERE advance_id = ?", (advance_id,))
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def get_monthly_advance_summary(year=None, month=None):
        """Get advance summary for reporting"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT 
                strftime('%Y-%m', date) as month,
                COUNT(*) as total_advances,
                SUM(amount) as total_amount,
                COUNT(CASE WHEN status = 'Pending' THEN 1 END) as pending_count,
                SUM(CASE WHEN status = 'Pending' THEN amount ELSE 0 END) as pending_amount
            FROM driver_advances
            WHERE 1=1
        '''
        params = []
        
        if year:
            query += " AND strftime('%Y', date) = ?"
            params.append(str(year))
        if month:
            query += " AND strftime('%m', date) = ?"
            params.append(str(month).zfill(2))
        
        query += " GROUP BY strftime('%Y-%m', date) ORDER BY month DESC"
        
        cursor.execute(query, params)
        summary = cursor.fetchall()
        conn.close()
        return summary