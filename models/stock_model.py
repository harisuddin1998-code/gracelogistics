from database.db_manager import get_db_connection
from datetime import datetime

class StockModel:
    
    @staticmethod
    def update_vehicle_stock(data):
        """Update daily vehicle stock (fuel, oil levels)"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO vehicle_stock 
            (vehicle_id, date, fuel_in_tank, oil_level, air_filter_status, oil_filter_status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['vehicle_id'], data['date'], data.get('fuel_in_tank'),
            data.get('oil_level', 'OK'), data.get('air_filter_status', 'OK'),
            data.get('oil_filter_status', 'OK'), data.get('notes', '')
        ))
        
        conn.commit()
        stock_id = cursor.lastrowid
        conn.close()
        return stock_id
    
    @staticmethod
    def get_latest_stock(vehicle_id):
        """Get latest stock entry for vehicle"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM vehicle_stock 
            WHERE vehicle_id = ? 
            ORDER BY date DESC LIMIT 1
        ''', (vehicle_id,))
        
        stock = cursor.fetchone()
        conn.close()
        return stock
    
    @staticmethod
    def get_stock_history(vehicle_id, days=30):
        """Get stock history for last N days"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM vehicle_stock 
            WHERE vehicle_id = ? 
            AND date >= date('now', ?)
            ORDER BY date DESC
        ''', (vehicle_id, f'-{days} days'))
        
        history = cursor.fetchall()
        conn.close()
        return history
    
    @staticmethod
    def get_low_oil_vehicles():
        """Get vehicles with low or critical oil"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT v.vehicle_id, v.registration_no, v.make, v.model, 
                   vs.oil_level, vs.date as last_check_date
            FROM vehicle_stock vs
            JOIN vehicles v ON vs.vehicle_id = v.vehicle_id
            WHERE vs.oil_level IN ('Low', 'Critical')
            AND vs.date = (
                SELECT MAX(date) FROM vehicle_stock 
                WHERE vehicle_id = v.vehicle_id
            )
        ''')
        
        vehicles = cursor.fetchall()
        conn.close()
        return vehicles