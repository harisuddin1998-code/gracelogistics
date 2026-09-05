from database.db_manager import get_db_connection
from datetime import datetime

class SalaryModel:
    
    @staticmethod
    def generate_salary_month(driver_id, month, data):
        """Generate salary record for a driver"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        net_payable = (data['base_salary'] + data['bonus'] - 
                      data['advance_deduction'] - data['penalty'])
        
        cursor.execute('''
            INSERT INTO salary_records 
            (driver_id, month, base_salary, advance_deduction, bonus, 
             penalty, net_payable, payment_date, payment_method, generated_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            driver_id, month, data['base_salary'], data['advance_deduction'],
            data['bonus'], data['penalty'], net_payable, 
            data.get('payment_date', datetime.now().strftime('%Y-%m-%d')),
            data['payment_method'], data.get('generated_by', 1)
        ))
        
        conn.commit()
        salary_id = cursor.lastrowid
        conn.close()
        return salary_id
    
    @staticmethod
    def get_salary_records(month=None, driver_id=None):
        """Get salary records with filters"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT s.*, d.full_name, d.license_no, d.phone, d.base_salary as driver_base_salary
            FROM salary_records s
            JOIN drivers d ON s.driver_id = d.driver_id
            WHERE 1=1
        '''
        params = []
        
        if month:
            query += " AND s.month = ?"
            params.append(month)
        if driver_id:
            query += " AND s.driver_id = ?"
            params.append(driver_id)
        
        query += " ORDER BY s.month DESC, d.full_name"
        
        cursor.execute(query, params)
        records = cursor.fetchall()
        conn.close()
        return records
    
    @staticmethod
    def get_salary_slip(salary_id):
        """Get single salary slip for printing"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT s.*, d.full_name, d.license_no, d.phone, d.address,
                   v.registration_no as assigned_vehicle
            FROM salary_records s
            JOIN drivers d ON s.driver_id = d.driver_id
            LEFT JOIN vehicles v ON d.driver_id = v.assigned_driver_id
            WHERE s.salary_id = ?
        ''', (salary_id,))
        
        record = cursor.fetchone()
        conn.close()
        return record
    
    @staticmethod
    def check_salary_generated(month, driver_id):
        """Check if salary already generated for this month and driver"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM salary_records 
            WHERE month = ? AND driver_id = ?
        ''', (month, driver_id))
        
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    
    @staticmethod
    def get_salary_by_id(salary_id):
        """Get salary record by ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT s.*, d.full_name, d.license_no, d.phone
            FROM salary_records s
            JOIN drivers d ON s.driver_id = d.driver_id
            WHERE s.salary_id = ?
        ''', (salary_id,))
        
        record = cursor.fetchone()
        conn.close()
        return record
    
    @staticmethod
    def update_salary(salary_id, data):
        """Update salary record"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        net_payable = (data['base_salary'] + data['bonus'] - 
                      data['advance_deduction'] - data['penalty'])
        
        cursor.execute('''
            UPDATE salary_records 
            SET base_salary = ?, advance_deduction = ?, bonus = ?, 
                penalty = ?, net_payable = ?, payment_date = ?, payment_method = ?
            WHERE salary_id = ?
        ''', (
            data['base_salary'], data['advance_deduction'], data['bonus'],
            data['penalty'], net_payable, data['payment_date'],
            data['payment_method'], salary_id
        ))
        
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def delete_salary(salary_id):
        """Delete a salary record"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM salary_records WHERE salary_id = ?", (salary_id,))
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def get_monthly_summary(year=None, month=None):
        """Get monthly salary summary"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT 
                strftime('%Y-%m', month) as salary_month,
                COUNT(*) as total_employees,
                SUM(base_salary) as total_base_salary,
                SUM(advance_deduction) as total_advance_deduction,
                SUM(bonus) as total_bonus,
                SUM(penalty) as total_penalty,
                SUM(net_payable) as total_net_payable
            FROM salary_records
            WHERE 1=1
        '''
        params = []
        
        if year:
            query += " AND strftime('%Y', month) = ?"
            params.append(str(year))
        if month:
            query += " AND strftime('%m', month) = ?"
            params.append(str(month).zfill(2))
        
        query += " GROUP BY strftime('%Y-%m', month) ORDER BY salary_month DESC"
        
        cursor.execute(query, params)
        summary = cursor.fetchall()
        conn.close()
        return summary
    
    @staticmethod
    def get_driver_salary_history(driver_id, limit=12):
        """Get salary history for a specific driver (last 12 months)"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM salary_records 
            WHERE driver_id = ?
            ORDER BY month DESC
            LIMIT ?
        ''', (driver_id, limit))
        
        records = cursor.fetchall()
        conn.close()
        return records
    
    @staticmethod
    def get_total_salary_expense(year=None, month=None):
        """Get total salary expense for a period"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT SUM(net_payable) as total FROM salary_records WHERE 1=1"
        params = []
        
        if year:
            query += " AND strftime('%Y', month) = ?"
            params.append(str(year))
        if month:
            query += " AND strftime('%m', month) = ?"
            params.append(str(month).zfill(2))
        
        cursor.execute(query, params)
        result = cursor.fetchone()
        conn.close()
        return result['total'] if result['total'] else 0
    
    @staticmethod
    def get_unpaid_advances_summary():
        """Get summary of unpaid advances that will affect next salaries"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                d.driver_id,
                d.full_name,
                d.base_salary,
                SUM(a.amount) as total_advance_pending
            FROM drivers d
            JOIN driver_advances a ON d.driver_id = a.driver_id
            WHERE a.status = 'Pending'
            GROUP BY d.driver_id
            ORDER BY total_advance_pending DESC
        ''')
        
        summary = cursor.fetchall()
        conn.close()
        return summary
    
    @staticmethod
    def get_salary_trend(last_n_months=6):
        """Get salary trend data for charts"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                strftime('%Y-%m', month) as salary_month,
                SUM(net_payable) as total_payable,
                COUNT(*) as employee_count,
                AVG(net_payable) as avg_salary
            FROM salary_records
            GROUP BY strftime('%Y-%m', month)
            ORDER BY salary_month DESC
            LIMIT ?
        ''', (last_n_months,))
        
        trend = cursor.fetchall()
        conn.close()
        return trend
    
    @staticmethod
    def get_salary_by_driver_and_month(driver_id, month):
        """Get salary record for specific driver and month"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM salary_records 
            WHERE driver_id = ? AND month = ?
        ''', (driver_id, month))
        
        record = cursor.fetchone()
        conn.close()
        return record
    
    @staticmethod
    def get_last_salary_date(driver_id):
        """Get last salary generation date for a driver"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT MAX(month) as last_month FROM salary_records 
            WHERE driver_id = ?
        ''', (driver_id,))
        
        result = cursor.fetchone()
        conn.close()
        return result['last_month'] if result else None
    
    @staticmethod
    def get_salary_stats():
        """Get salary statistics for dashboard"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Total salary records
        cursor.execute("SELECT COUNT(*) FROM salary_records")
        stats['total_records'] = cursor.fetchone()[0]
        
        # Total salary paid (all time)
        cursor.execute("SELECT SUM(net_payable) FROM salary_records")
        result = cursor.fetchone()
        stats['total_paid'] = result[0] if result[0] else 0
        
        # Current month salary
        current_month = datetime.now().strftime('%Y-%m')
        cursor.execute('''
            SELECT SUM(net_payable) FROM salary_records WHERE month = ?
        ''', (current_month,))
        result = cursor.fetchone()
        stats['current_month_total'] = result[0] if result[0] else 0
        
        # Current month employee count
        cursor.execute('''
            SELECT COUNT(DISTINCT driver_id) FROM salary_records WHERE month = ?
        ''', (current_month,))
        stats['current_month_employees'] = cursor.fetchone()[0]
        
        # Average salary
        cursor.execute("SELECT AVG(net_payable) FROM salary_records")
        result = cursor.fetchone()
        stats['average_salary'] = result[0] if result[0] else 0
        
        conn.close()
        return stats