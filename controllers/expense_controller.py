from flask import Blueprint, render_template, request, redirect, url_for, flash, session, make_response
from functools import wraps
from models.expense_model import ExpenseModel
from models.vehicle_model import VehicleModel
from models.vendor_model import VendorModel
from datetime import datetime
import pandas as pd
from io import BytesIO
from utils.helpers import form_text, form_text_or_none, form_float, form_int, form_date, form_id

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
                'vehicle_id': form_id(request.form, 'vehicle_id'),
                'part_id': form_id(request.form, 'part_id'),
                'vendor_id': form_id(request.form, 'vendor_id'),
                'date': form_date(request.form, 'date'),
                'quantity_used': form_int(request.form, 'quantity_used'),
                'mechanic_name': form_text(request.form, 'mechanic_name'),
                'failure_reason': form_text(request.form, 'failure_reason'),
                'warranty_until': form_date(request.form, 'warranty_until')
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

# Filters behind the clickable boxes on the inventory: ?filter=<key>
# (same rules as the counts in ExpenseModel.get_inventory_stats)
INVENTORY_FILTERS = {
    'low': ('Low stock (at or below reorder level)', lambda i: (i['quantity_in_stock'] or 0) <= (i['reorder_level'] or 0)),
    'out': ('Out of stock', lambda i: (i['quantity_in_stock'] or 0) <= 0),
}


@expense_bp.route('/inventory')
@login_required
def inventory():
    all_items = ExpenseModel.get_inventory()
    stats = ExpenseModel.get_inventory_stats()

    active_filter = request.args.get('filter', '')
    inventory, filter_label = all_items, None
    if active_filter in INVENTORY_FILTERS:
        filter_label, keep = INVENTORY_FILTERS[active_filter]
        inventory = [i for i in all_items if keep(i)]
    else:
        active_filter = ''

    return render_template('expenses/inventory.html', inventory=inventory, stats=stats,
                           active_filter=active_filter, filter_label=filter_label)


@expense_bp.route('/inventory/add', methods=['GET', 'POST'])
@login_required
def add_inventory():
    if request.method == 'POST':
        try:
            data = {
                'part_name': form_text(request.form, 'part_name'),
                # NULL (not '') when blank so several parts can be saved without a part number
                'part_number': form_text_or_none(request.form, 'part_number'),
                'category': form_text_or_none(request.form, 'category'),
                'quantity_in_stock': form_int(request.form, 'quantity_in_stock'),
                'reorder_level': form_int(request.form, 'reorder_level'),
                'unit_cost': form_float(request.form, 'unit_cost'),
                'selling_price': form_float(request.form, 'selling_price'),
                'location': form_text(request.form, 'location'),
                'supplier_name': form_text(request.form, 'supplier_name'),
                'last_ordered_date': form_date(request.form, 'last_ordered_date')
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
                'part_name': form_text(request.form, 'part_name'),
                'part_number': form_text_or_none(request.form, 'part_number'),
                'category': form_text_or_none(request.form, 'category'),
                'reorder_level': form_int(request.form, 'reorder_level'),
                'unit_cost': form_float(request.form, 'unit_cost'),
                'selling_price': form_float(request.form, 'selling_price'),
                'location': form_text(request.form, 'location'),
                'supplier_name': form_text(request.form, 'supplier_name')
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
    quantity = form_int(request.form, 'quantity')
    operation = form_text(request.form, 'operation', 'add')
    
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
        LEFT JOIN spare_parts_inventory p ON e.part_id = p.part_id
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