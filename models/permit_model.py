from database.db_manager import get_db_connection
from datetime import datetime, timedelta

class PermitModel:
    
    @staticmethod
    def add_permit(data):
        """Add road permit record"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO road_permits 
            (vehicle_id, issue_date, expiry_date, renewal_date, cost, authority_name, document_image)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['vehicle_id'], data['issue_date'], data['expiry_date'],
            data.get('renewal_date'), data.get('cost', 0),
            data.get('authority_name'), data.get('document_image', '')
        ))
        
        conn.commit()
        permit_id = cursor.lastrowid
        conn.close()
        return permit_id
    
    @staticmethod
    def update_permit(permit_id, data):
        """Update permit (renewal)"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE road_permits 
            SET expiry_date = ?, renewal_date = ?, cost = ?, document_image = ?
            WHERE permit_id = ?
        ''', (
            data['expiry_date'], datetime.now().strftime('%Y-%m-%d'),
            data['cost'], data.get('document_image', ''), permit_id
        ))
        
        conn.commit()
        conn.close()
        return True

    @staticmethod
    def full_update_permit(permit_id, data):
        """Update full permit details"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE road_permits 
            SET vehicle_id = ?, issue_date = ?, expiry_date = ?, renewal_date = ?,
                cost = ?, authority_name = ?, document_image = ?
            WHERE permit_id = ?
        ''', (
            data['vehicle_id'], data['issue_date'], data['expiry_date'],
            data.get('renewal_date'), data.get('cost', 0),
            data.get('authority_name', ''), data.get('document_image', ''), permit_id
        ))
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def get_all_permits():
        """Get all permits with vehicle info"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.*, v.registration_no, v.make, v.model,
                   CAST(julianday(p.expiry_date) - julianday('now') AS INTEGER) as days_until_expiry
            FROM road_permits p
            JOIN vehicles v ON p.vehicle_id = v.vehicle_id
            ORDER BY p.expiry_date ASC
        ''')
        
        permits = cursor.fetchall()
        conn.close()
        return permits
    
    @staticmethod
    def get_expiring_permits(days=15):
        """Get permits expiring within N days"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.*, v.registration_no, v.make, v.model,
                   CAST(julianday(p.expiry_date) - julianday('now') AS INTEGER) as days_left
            FROM road_permits p
            JOIN vehicles v ON p.vehicle_id = v.vehicle_id
            WHERE julianday(p.expiry_date) - julianday('now') <= ?
            AND julianday(p.expiry_date) - julianday('now') >= 0
            ORDER BY days_left ASC
        ''', (days,))
        
        permits = cursor.fetchall()
        conn.close()
        return permits
    
    @staticmethod
    def get_permit_by_vehicle(vehicle_id):
        """Get current permit for vehicle"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM road_permits 
            WHERE vehicle_id = ? 
            ORDER BY expiry_date DESC LIMIT 1
        ''', (vehicle_id,))
        
        permit = cursor.fetchone()
        conn.close()
        return permit
    
    @staticmethod
    def get_permit_by_id(permit_id):
        """Get permit by ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.*, v.registration_no, v.make, v.model
            FROM road_permits p
            JOIN vehicles v ON p.vehicle_id = v.vehicle_id
            WHERE p.permit_id = ?
        ''', (permit_id,))
        
        permit = cursor.fetchone()
        conn.close()
        return permit
    
    @staticmethod
    def delete_permit(permit_id):
        """Delete a permit record"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM road_permits WHERE permit_id = ?", (permit_id,))
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def get_expired_permits():
        """Get all expired permits"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.*, v.registration_no, v.make, v.model,
                   CAST(julianday('now') - julianday(p.expiry_date) AS INTEGER) as days_expired
            FROM road_permits p
            JOIN vehicles v ON p.vehicle_id = v.vehicle_id
            WHERE julianday(p.expiry_date) - julianday('now') < 0
            ORDER BY p.expiry_date ASC
        ''')
        
        permits = cursor.fetchall()
        conn.close()
        return permits
    
    @staticmethod
    def get_permit_summary():
        """Get permit summary statistics"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        summary = {}
        
        # Total permits
        cursor.execute("SELECT COUNT(*) FROM road_permits")
        summary['total_permits'] = cursor.fetchone()[0]
        
        # Expired permits
        cursor.execute("SELECT COUNT(*) FROM road_permits WHERE julianday(expiry_date) - julianday('now') < 0")
        summary['expired_permits'] = cursor.fetchone()[0]
        
        # Expiring in 30 days
        cursor.execute("SELECT COUNT(*) FROM road_permits WHERE julianday(expiry_date) - julianday('now') BETWEEN 0 AND 30")
        summary['expiring_soon'] = cursor.fetchone()[0]
        
        # Valid permits
        cursor.execute("SELECT COUNT(*) FROM road_permits WHERE julianday(expiry_date) - julianday('now') > 30")
        summary['valid_permits'] = cursor.fetchone()[0]
        
        conn.close()
        return summary