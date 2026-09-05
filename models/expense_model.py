from database.db_manager import get_db_connection
from datetime import datetime

class ExpenseModel:
    
    # ============================================
    # SPARE PARTS INVENTORY
    # ============================================
    
    @staticmethod
    def get_inventory():
        """Get all spare parts inventory"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT *, 
                   CASE 
                       WHEN quantity_in_stock <= 0 THEN 'Out of Stock'
                       WHEN quantity_in_stock <= reorder_level THEN 'Low Stock'
                       ELSE 'In Stock'
                   END as stock_status
            FROM spare_parts_inventory
            ORDER BY part_name
        ''')
        inventory = cursor.fetchall()
        conn.close()
        return inventory
    
    @staticmethod
    def get_inventory_item(part_id):
        """Get single inventory item"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM spare_parts_inventory WHERE part_id = ?', (part_id,))
        item = cursor.fetchone()
        conn.close()
        return item
    
    @staticmethod
    def add_inventory_item(data):
        """Add new spare part"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO spare_parts_inventory 
            (part_name, part_number, category, quantity_in_stock, reorder_level, 
             unit_cost, selling_price, location, supplier_name, last_ordered_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['part_name'], data['part_number'], data['category'], 
            data['quantity_in_stock'], data['reorder_level'],
            data['unit_cost'], data.get('selling_price', 0),
            data.get('location', ''), data.get('supplier_name', ''),
            data.get('last_ordered_date')
        ))
        
        conn.commit()
        part_id = cursor.lastrowid
        conn.close()
        return part_id
    
    @staticmethod
    def update_inventory_item(part_id, data):
        """Update inventory item"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE spare_parts_inventory 
            SET part_name = ?, part_number = ?, category = ?, 
                reorder_level = ?, unit_cost = ?, selling_price = ?,
                location = ?, supplier_name = ?
            WHERE part_id = ?
        ''', (
            data['part_name'], data['part_number'], data['category'],
            data['reorder_level'], data['unit_cost'], data.get('selling_price', 0),
            data.get('location', ''), data.get('supplier_name', ''), part_id
        ))
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def update_stock(part_id, quantity, operation='add'):
        """Update stock quantity"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if operation == 'add':
            cursor.execute('''
                UPDATE spare_parts_inventory 
                SET quantity_in_stock = quantity_in_stock + ?,
                    last_ordered_date = ?
                WHERE part_id = ?
            ''', (quantity, datetime.now().strftime('%Y-%m-%d'), part_id))
        else:
            cursor.execute('''
                UPDATE spare_parts_inventory 
                SET quantity_in_stock = quantity_in_stock - ?
                WHERE part_id = ? AND quantity_in_stock >= ?
            ''', (quantity, part_id, quantity))
        
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def delete_inventory_item(part_id):
        """Delete inventory item"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM spare_parts_inventory WHERE part_id = ?", (part_id,))
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def get_low_stock_items():
        """Get low stock items"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM spare_parts_inventory 
            WHERE quantity_in_stock <= reorder_level AND quantity_in_stock > 0
        ''')
        items = cursor.fetchall()
        conn.close()
        return items
    
    @staticmethod
    def get_inventory_stats():
        """Get inventory statistics"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM spare_parts_inventory")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM spare_parts_inventory WHERE quantity_in_stock <= reorder_level")
        low_stock = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM spare_parts_inventory WHERE quantity_in_stock <= 0")
        out_of_stock = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(quantity_in_stock * unit_cost) FROM spare_parts_inventory")
        total_value = cursor.fetchone()[0] or 0
        
        conn.close()
        return {
            'total_parts': total,
            'low_stock_count': low_stock,
            'out_of_stock_count': out_of_stock,
            'total_value': total_value
        }
    
    # ============================================
    # SPARE PARTS EXPENSE
    # ============================================
    
    @staticmethod
    def add_expense(data):
        """Add spare parts expense"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get part price
        cursor.execute("SELECT unit_cost FROM spare_parts_inventory WHERE part_id = ?", (data['part_id'],))
        part = cursor.fetchone()
        unit_price = part['unit_cost'] if part else 0
        total_cost = data['quantity_used'] * unit_price
        
        # Update stock
        cursor.execute('''
            UPDATE spare_parts_inventory 
            SET quantity_in_stock = quantity_in_stock - ?
            WHERE part_id = ?
        ''', (data['quantity_used'], data['part_id']))
        
        # Add expense
        cursor.execute('''
            INSERT INTO spare_parts_expense 
            (vehicle_id, part_id, vendor_id, date, quantity_used, unit_price, total_cost, 
             mechanic_name, failure_reason, warranty_until)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['vehicle_id'], data['part_id'], data.get('vendor_id'),
            data['date'], data['quantity_used'], unit_price, total_cost,
            data.get('mechanic_name', ''), data.get('failure_reason', ''),
            data.get('warranty_until')
        ))
        
        conn.commit()
        expense_id = cursor.lastrowid
        conn.close()
        return expense_id
    
    @staticmethod
    def get_expenses(vehicle_id=None, start_date=None, end_date=None):
        """Get expense history"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT e.*, v.registration_no, v.make, v.model,
                   p.part_name, p.part_number
            FROM spare_parts_expense e
            JOIN vehicles v ON e.vehicle_id = v.vehicle_id
            JOIN spare_parts_inventory p ON e.part_id = p.part_id
            WHERE 1=1
        '''
        params = []
        
        if vehicle_id:
            query += " AND e.vehicle_id = ?"
            params.append(vehicle_id)
        if start_date:
            query += " AND e.date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND e.date <= ?"
            params.append(end_date)
        
        query += " ORDER BY e.date DESC"
        
        cursor.execute(query, params)
        expenses = cursor.fetchall()
        conn.close()
        return expenses
    
    @staticmethod
    def delete_expense(expense_id):
        """Delete expense and restore stock"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get expense details
        cursor.execute("SELECT part_id, quantity_used FROM spare_parts_expense WHERE expense_id = ?", (expense_id,))
        expense = cursor.fetchone()
        
        if expense:
            # Restore stock
            cursor.execute('''
                UPDATE spare_parts_inventory 
                SET quantity_in_stock = quantity_in_stock + ?
                WHERE part_id = ?
            ''', (expense['quantity_used'], expense['part_id']))
        
        cursor.execute("DELETE FROM spare_parts_expense WHERE expense_id = ?", (expense_id,))
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def get_total_expense(vehicle_id=None):
        """Get total expense"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "SELECT SUM(total_cost) as total FROM spare_parts_expense WHERE 1=1"
        params = []
        
        if vehicle_id:
            query += " AND vehicle_id = ?"
            params.append(vehicle_id)
        
        cursor.execute(query, params)
        result = cursor.fetchone()
        conn.close()
        return result['total'] if result['total'] else 0