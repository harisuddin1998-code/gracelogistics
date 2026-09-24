from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from functools import wraps
from models.driver_model import DriverModel
from models.vehicle_model import VehicleModel
from models.advance_model import AdvanceModel
from datetime import date, datetime
from utils.helpers import form_text, form_text_or_none, form_float, form_date, form_id

driver_bp = Blueprint('driver', __name__, url_prefix='/drivers')

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('auth_login'))
        return f(*args, **kwargs)
    return decorated_function


def _driver_form_data():
    """Read the driver form; blank/missing fields never raise."""
    return {
        'full_name': form_text(request.form, 'full_name'),
        # NULL (not '') when blank so several drivers can be saved without a licence number
        'license_no': form_text_or_none(request.form, 'license_no'),
        'phone': form_text(request.form, 'phone'),
        'address': form_text(request.form, 'address'),
        'joining_date': form_date(request.form, 'joining_date'),
        'base_salary': form_float(request.form, 'base_salary'),
        'status': form_text(request.form, 'status', 'Active')
    }


# Filters behind the clickable boxes on the driver list: ?filter=<key>
DRIVER_FILTERS = {
    'active': ('Active drivers', lambda d: d['status'] == 'Active'),
    'inactive': ('Inactive drivers', lambda d: d['status'] == 'Inactive'),
    'assigned': ('Drivers assigned to a vehicle', lambda d: bool(d['vehicle_count'])),
    'advance': ('Drivers with an advance balance', lambda d: (d['advance_balance'] or 0) > 0),
}


@driver_bp.route('/')
@login_required
def list_drivers():
    all_drivers = DriverModel.get_all_drivers()

    active_filter = request.args.get('filter', '')
    drivers, filter_label = all_drivers, None
    if active_filter in DRIVER_FILTERS:
        filter_label, keep = DRIVER_FILTERS[active_filter]
        drivers = [d for d in all_drivers if keep(d)]
    else:
        active_filter = ''

    # box counts always describe the whole fleet, not the filtered rows
    stats = {
        'total': len(all_drivers),
        'active': sum(1 for d in all_drivers if d['status'] == 'Active'),
        'assigned': sum(1 for d in all_drivers if d['vehicle_count']),
        'advance': sum((d['advance_balance'] or 0) for d in all_drivers),
    }
    return render_template('drivers/list.html', drivers=drivers, stats=stats,
                           active_filter=active_filter, filter_label=filter_label)


@driver_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_driver():
    if request.method == 'POST':
        data = _driver_form_data()
        
        driver_id = DriverModel.add_driver(data)
        flash('Driver added successfully!', 'success')
        return redirect(url_for('driver.list_drivers'))
    
    return render_template('drivers/add.html')


@driver_bp.route('/edit/<int:driver_id>', methods=['GET', 'POST'])
@login_required
def edit_driver(driver_id):
    driver = DriverModel.get_driver_by_id(driver_id)
    if not driver:
        flash('Driver not found!', 'danger')
        return redirect(url_for('driver.list_drivers'))
    
    if request.method == 'POST':
        data = _driver_form_data()
        
        DriverModel.update_driver(driver_id, data)
        flash('Driver updated successfully!', 'success')
        return redirect(url_for('driver.list_drivers'))
    
    return render_template('drivers/edit.html', driver=driver)


@driver_bp.route('/delete/<int:driver_id>')
@login_required
def delete_driver(driver_id):
    DriverModel.delete_driver(driver_id)
    flash('Driver deleted successfully!', 'success')
    return redirect(url_for('driver.list_drivers'))


# ============================================
# ADVANCE SALARY SECTION - COMPLETE
# ============================================

@driver_bp.route('/advance', methods=['GET', 'POST'])
@login_required
def advance_salary():
    if request.method == 'POST':
        driver_id = form_id(request.form, 'driver_id')
        amount = form_float(request.form, 'amount')
        reason = form_text(request.form, 'reason')
        advance_date = form_date(request.form, 'date')
        
        # Check if amount exceeds 50% of salary
        driver = DriverModel.get_driver_by_id(driver_id) if driver_id else None
        max_advance = ((driver['base_salary'] or 0) * 0.5) if driver else 0
        if driver and amount > max_advance:
            flash(f'Advance amount cannot exceed 50% of salary (PKR {max_advance:.2f})', 'danger')
            return redirect(url_for('driver.advance_salary'))
        
        data = {
            'driver_id': driver_id,
            'date': advance_date,
            'amount': amount,
            'reason': reason,
            'status': 'Pending'
        }
        
        AdvanceModel.add_advance(data)
        if driver_id:
            DriverModel.update_advance_balance(driver_id, amount, 'add')
        
        flash(f'Advance salary of PKR {amount:,.2f} recorded successfully!', 'success')
        return redirect(url_for('driver.advance_salary'))
    
    drivers = DriverModel.get_all_drivers()
    pending_advances = AdvanceModel.get_pending_advances()
    advance_history = AdvanceModel.get_all_advances()
    
    return render_template('drivers/advance_salary.html', 
                         drivers=drivers,
                         pending_advances=pending_advances,
                         advance_history=advance_history,
                         today=date.today().strftime('%Y-%m-%d'))


@driver_bp.route('/advance/edit/<int:advance_id>', methods=['GET', 'POST'])
@login_required
def edit_advance(advance_id):
    advance = AdvanceModel.get_advance_by_id(advance_id)
    if not advance:
        flash('Advance record not found!', 'danger')
        return redirect(url_for('driver.advance_salary'))
    
    if request.method == 'POST':
        amount = form_float(request.form, 'amount')
        reason = form_text(request.form, 'reason')
        advance_date = form_date(request.form, 'date')
        
        # Update driver balance
        old_amount = advance['amount'] or 0
        if amount != old_amount and advance['driver_id']:
            difference = amount - old_amount
            if difference > 0:
                DriverModel.update_advance_balance(advance['driver_id'], difference, 'add')
            else:
                DriverModel.update_advance_balance(advance['driver_id'], abs(difference), 'deduct')
        
        AdvanceModel.update_advance(advance_id, {
            'amount': amount,
            'reason': reason,
            'date': advance_date
        })
        
        flash('Advance record updated successfully!', 'success')
        return redirect(url_for('driver.advance_salary'))
    
    drivers = DriverModel.get_all_drivers()
    return render_template('drivers/edit_advance.html', advance=advance, drivers=drivers)


@driver_bp.route('/advance/mark-deducted/<int:advance_id>')
@login_required
def mark_advance_deducted(advance_id):
    advance = AdvanceModel.get_advance_by_id(advance_id)
    if advance:
        current_month = date.today().strftime('%Y-%m')
        AdvanceModel.mark_deducted(advance_id, current_month)
        DriverModel.update_advance_balance(advance['driver_id'], advance['amount'] or 0, 'deduct')
        flash('Advance marked as deducted from salary!', 'success')
    else:
        flash('Advance record not found!', 'danger')
    
    return redirect(url_for('driver.advance_salary'))


@driver_bp.route('/advance/delete/<int:advance_id>')
@login_required
def delete_advance(advance_id):
    advance = AdvanceModel.get_advance_by_id(advance_id)
    if advance:
        AdvanceModel.delete_advance(advance_id)
        flash('Advance record deleted successfully!', 'success')
    else:
        flash('Advance record not found!', 'danger')
    
    return redirect(url_for('driver.advance_salary'))


@driver_bp.route('/advance/pay-back/<int:advance_id>')
@login_required
def pay_back_advance(advance_id):
    advance = AdvanceModel.get_advance_by_id(advance_id)
    if advance:
        AdvanceModel.mark_paid_back(advance_id)
        DriverModel.update_advance_balance(advance['driver_id'], advance['amount'] or 0, 'deduct')
        flash('Advance marked as paid back!', 'success')
    else:
        flash('Advance record not found!', 'danger')
    
    return redirect(url_for('driver.advance_salary'))


@driver_bp.route('/api/stats')
@login_required
def api_driver_stats():
    stats = DriverModel.get_driver_stats()
    return jsonify(stats)


@driver_bp.route('/api/advances')
@login_required
def api_advances():
    pending = AdvanceModel.get_pending_advances()
    return jsonify([dict(a) for a in pending])