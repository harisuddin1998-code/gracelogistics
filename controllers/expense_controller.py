from flask import Blueprint, render_template, request, redirect, url_for, flash, session, make_response
from functools import wraps
from models.expense_model import ExpenseModel
from models.vehicle_model import VehicleModel
from models.vendor_model import VendorModel
from datetime import datetime
import pandas as pd
from io import BytesIO

expense_bp = Blueprint('expense', __name__, url_prefix='/expenses')

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('auth_login'))
        return f(*args, **kwargs)
    return decorated_function


# ============================================
# SPARE PARTS EXPENSE ROUTES
# ============================================

@expense_bp.route('/spare-parts', methods=['GET', 'POST'])
@login_required
def spare_parts():
    if request.method == 'POST':
        try:
            data = {
                'vehicle_id': request.form['vehicle_id'],
                'part_id': request.form['part_id'],
                'vendor_id': request.form.get('vendor_id'),
                'date': request.form['date'],
                'quantity_used': int(request.form['quantity_used']),
                'mechanic_name': request.form.get('mechanic_name', ''),
                'failure_reason': request.form.get('failure_reason', ''),
                'warranty_until': request.form.get('warranty_until') if request.form.get('warranty_until') else None
            }
            
            ExpenseModel.add_expense(data)
            flash('Spare part expense recorded successfully!', 'success')
            return redirect(url_for('expense.spare_parts'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('expense.spare_parts'))
    
    vehicles = VehicleModel.get_all_vehicles()
    inventory = ExpenseModel.get_inventory()
    vendors = VendorModel.get_all_vendors()
    return render_template('expenses/spare_parts.html', 
                         vehicles=vehicles, 
                         inventory=inventory,
                         vendors=vendors,
                         today=datetime.now().strftime('%Y-%m-%d'))


@expense_bp.route('/history')
@login_required
def expense_history():
    vehicle_id = request.args.get('vehicle_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Use the correct method name: get_expenses (not get_spare_parts_expenses)
    expenses = ExpenseModel.get_expenses(vehicle_id, start_date, end_date)
    vehicles = VehicleModel.get_all_vehicles()
    inventory = ExpenseModel.get_inventory()
    
    total = ExpenseModel.get_total_expense(vehicle_id)
    
    return render_template('expenses/history.html', 
                         expenses=expenses, 
                         vehicles=vehicles,
                         inventory=inventory,
                         total=total,
                         selected_vehicle=vehicle_id,
                         start_date=start_date,
                         end_date=end_date)


@expense_bp.route('/delete/<int:expense_id>')
@login_required
def delete_expense(expense_id):
    ExpenseModel.delete_expense(expense_id)
    flash('Expense record deleted and stock restored!', 'success')
    return redirect(url_for('expense.expense_history'))


# ============================================
# INVENTORY MANAGEMENT ROUTES
# ============================================

@expense_bp.route('/inventory')
@login_required
def inventory():
    inventory = ExpenseModel.get_inventory()
    stats = ExpenseModel.get_inventory_stats()
    return render_template('expenses/inventory.html', inventory=inventory, stats=stats)


@expense_bp.route('/inventory/add', methods=['GET', 'POST'])
@login_required
def add_inventory():
    if request.method == 'POST':
        try:
            data = {
                'part_name': request.form['part_name'],
                'part_number': request.form['part_number'],
                'category': request.form['category'],
                'quantity_in_stock': int(request.form['quantity_in_stock']),
                'reorder_level': int(request.form['reorder_level']),
                'unit_cost': float(request.form['unit_cost']),
                'selling_price': float(request.form.get('selling_price', 0)),
                'location': request.form.get('location', ''),
                'supplier_name': request.form.get('supplier_name', ''),
                'last_ordered_date': request.form.get('last_ordered_date') if request.form.get('last_ordered_date') else None
            }
            
            ExpenseModel.add_inventory_item(data)
            flash('New spare part added to inventory!', 'success')
            return redirect(url_for('expense.inventory'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('expense.add_inventory'))
    
    return render_template('expenses/add_inventory.html')


@expense_bp.route('/inventory/edit/<int:part_id>', methods=['GET', 'POST'])
@login_required
def edit_inventory(part_id):
    item = ExpenseModel.get_inventory_item(part_id)
    if not item:
        flash('Item not found!', 'danger')
        return redirect(url_for('expense.inventory'))
    
    if request.method == 'POST':
        try:
            data = {
                'part_name': request.form['part_name'],
                'part_number': request.form['part_number'],
                'category': request.form['category'],
                'reorder_level': int(request.form['reorder_level']),
                'unit_cost': float(request.form['unit_cost']),
                'selling_price': float(request.form.get('selling_price', 0)),
                'location': request.form.get('location', ''),
                'supplier_name': request.form.get('supplier_name', '')
            }
            
            ExpenseModel.update_inventory_item(part_id, data)
            flash('Inventory item updated successfully!', 'success')
            return redirect(url_for('expense.inventory'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('expense.edit_inventory', part_id=part_id))
    
    return render_template('expenses/edit_inventory.html', item=item)


@expense_bp.route('/inventory/delete/<int:part_id>')
@login_required
def delete_inventory(part_id):
    ExpenseModel.delete_inventory_item(part_id)
    flash('Inventory item deleted successfully!', 'success')
    return redirect(url_for('expense.inventory'))


@expense_bp.route('/inventory/stock/<int:part_id>', methods=['POST'])
@login_required
def update_stock(part_id):
    quantity = int(request.form['quantity'])
    operation = request.form['operation']
    
    ExpenseModel.update_stock(part_id, quantity, operation)
    flash(f'Stock updated successfully!', 'success')
    return redirect(url_for('expense.inventory'))


# ============================================
# REPORT ROUTES
# ============================================

@expense_bp.route('/report')
@login_required
def report():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    expenses = ExpenseModel.get_expenses(start_date=start_date, end_date=end_date)
    total_cost = ExpenseModel.get_total_expense()
    stats = ExpenseModel.get_inventory_stats()
    
    # Get most used parts - query directly
    from database.db_manager import get_db_connection
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            p.part_name,
            p.part_number,
            COUNT(e.expense_id) as usage_count,
            SUM(e.quantity_used) as total_quantity,
            SUM(e.total_cost) as total_cost
        FROM spare_parts_expense e
        JOIN spare_parts_inventory p ON e.part_id = p.part_id
        GROUP BY p.part_id
        ORDER BY total_quantity DESC
        LIMIT 10
    ''')
    most_used = cursor.fetchall()
    conn.close()
    
    return render_template('expenses/report.html', 
                         expenses=expenses,
                         total_cost=total_cost,
                         stats=stats,
                         most_used=most_used,
                         start_date=start_date,
                         end_date=end_date)


@expense_bp.route('/export-excel')
@login_required
def export_excel():
    """Export spare parts expenses to Excel"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    expenses = ExpenseModel.get_expenses(start_date=start_date, end_date=end_date)
    inventory = ExpenseModel.get_inventory()
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Expenses Sheet
        if expenses:
            df_expenses = pd.DataFrame([dict(r) for r in expenses])
            df_expenses.to_excel(writer, sheet_name='Expenses', index=False)
        
        # Inventory Sheet
        if inventory:
            df_inventory = pd.DataFrame([dict(r) for r in inventory])
            df_inventory.to_excel(writer, sheet_name='Inventory', index=False)
    
    output.seek(0)
    filename = f'spare_parts_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    return make_response(
        output.getvalue(),
        200,
        {
            'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'Content-Disposition': f'attachment; filename={filename}'
        }
    )


# ============================================
# API ENDPOINTS
# ============================================

@expense_bp.route('/api/low-stock')
@login_required
def api_low_stock():
    low_stock = ExpenseModel.get_low_stock_items()
    return {'low_stock': [dict(item) for item in low_stock]}


@expense_bp.route('/api/stats')
@login_required
def api_stats():
    stats = ExpenseModel.get_inventory_stats()
    return stats