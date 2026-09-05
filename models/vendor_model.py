from database.db_manager import get_db_connection

class VendorModel:
    
    @staticmethod
    def get_all_vendors():
        """Get all vendors"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM vendors ORDER BY vendor_name')
        vendors = cursor.fetchall()
        conn.close()
        return vendors
    
    @staticmethod
    def get_vendor_by_id(vendor_id):
        """Get vendor by ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM vendors WHERE vendor_id = ?', (vendor_id,))
        vendor = cursor.fetchone()
        conn.close()
        return vendor
    
    @staticmethod
    def add_vendor(data):
        """Add new vendor"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO vendors (vendor_name, contact_person, phone, email, address, tax_number, payment_terms, rating)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (data['vendor_name'], data.get('contact_person', ''), data.get('phone', ''),
              data.get('email', ''), data.get('address', ''), data.get('tax_number', ''),
              data.get('payment_terms', ''), data.get('rating', 3)))
        conn.commit()
        vendor_id = cursor.lastrowid
        conn.close()
        return vendor_id
    
    @staticmethod
    def update_vendor(vendor_id, data):
        """Update vendor"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE vendors SET vendor_name=?, contact_person=?, phone=?, email=?, 
            address=?, tax_number=?, payment_terms=?, rating=?, is_active=?
            WHERE vendor_id=?
        ''', (data['vendor_name'], data.get('contact_person', ''), data.get('phone', ''),
              data.get('email', ''), data.get('address', ''), data.get('tax_number', ''),
              data.get('payment_terms', ''), data.get('rating', 3), data.get('is_active', 1), vendor_id))
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def delete_vendor(vendor_id):
        """Delete vendor"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM vendors WHERE vendor_id = ?', (vendor_id,))
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def get_vendor_stats():
        """Get vendor statistics"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM vendors WHERE is_active = 1')
        active = cursor.fetchone()[0]
        
        cursor.execute('SELECT AVG(rating) FROM vendors WHERE is_active = 1')
        avg_rating = cursor.fetchone()[0] or 0
        
        conn.close()
        return {'active_vendors': active, 'avg_rating': round(avg_rating, 1)}