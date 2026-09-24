from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
from models.permit_model import PermitModel
from models.vehicle_model import VehicleModel
from database.db_manager import get_db_connection
from datetime import datetime, timedelta
from utils.helpers import form_text, form_float, form_date, form_id

permit_bp = Blueprint('permit', __name__, url_prefix='/permits')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('auth_login'))
        return f(*args, **kwargs)
    return decorated_function

def _permit_form_data():
    """Read the permit form; blank/missing fields never raise."""
    return {
        'vehicle_id': form_id(request.form, 'vehicle_id'),
        'issue_date': form_date(request.form, 'issue_date'),
        'expiry_date': form_date(request.form, 'expiry_date'),
        'renewal_date': form_date(request.form, 'renewal_date'),
        'cost': form_float(request.form, 'cost'),
        'authority_name': form_text(request.form, 'authority_name'),
        'document_image': ''
    }


# Filters behind the clickable boxes on the permit list: ?filter=<key>
# (days_until_expiry is None when a permit was saved without an expiry date)
PERMIT_FILTERS = {
    'valid': ('Valid permits (30+ days left)', lambda p: p['days_until_expiry'] is not None and p['days_until_expiry'] >= 30),
    'expiring': ('Permits expiring within 30 days', lambda p: p['days_until_expiry'] is not None and 0 <= p['days_until_expiry'] < 30),
    'expired': ('Expired permits', lambda p: p['days_until_expiry'] is not None and p['days_until_expiry'] < 0),
}


@permit_bp.route('/')
@login_required
def list_permits():
    all_permits = PermitModel.get_all_permits()
    expiring_soon = PermitModel.get_expiring_permits(15)

    active_filter = request.args.get('filter', '')
    permits, filter_label = all_permits, None
    if active_filter in PERMIT_FILTERS:
        filter_label, keep = PERMIT_FILTERS[active_filter]
        permits = [p for p in all_permits if keep(p)]
    else:
        active_filter = ''

    return render_template('permits/list.html', permits=permits, all_permits=all_permits,
                           expiring_soon=expiring_soon, active_filter=active_filter,
                           filter_label=filter_label)

@permit_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_permit():
    if request.method == 'POST':
        try:
            data = _permit_form_data()
            
            PermitModel.add_permit(data)
            flash('Road permit added successfully!', 'success')
            return redirect(url_for('permit.list_permits'))
        except Exception as e:
            flash(f'Error adding permit: {str(e)}', 'danger')
            return redirect(url_for('permit.add_permit'))
    
    vehicles = VehicleModel.get_all_vehicles()
    return render_template('permits/add.html', vehicles=vehicles, 
                         today=datetime.now().strftime('%Y-%m-%d'))

@permit_bp.route('/edit/<int:permit_id>', methods=['GET', 'POST'])
@login_required
def edit_permit(permit_id):
    permit = PermitModel.get_permit_by_id(permit_id)
    if not permit:
        flash('Permit record not found!', 'danger')
        return redirect(url_for('permit.list_permits'))
    
    if request.method == 'POST':
        try:
            data = _permit_form_data()
            PermitModel.full_update_permit(permit_id, data)
            flash('Permit updated successfully!', 'success')
            return redirect(url_for('permit.list_permits'))
        except Exception as e:
            flash(f'Error updating permit: {str(e)}', 'danger')
            return redirect(url_for('permit.edit_permit', permit_id=permit_id))

    vehicles = VehicleModel.get_all_vehicles()
    return render_template('permits/add.html', permit=permit, vehicles=vehicles, is_edit=True)

@permit_bp.route('/renew/<int:permit_id>', methods=['GET', 'POST'])
@login_required
def renew_permit(permit_id):
    permit = PermitModel.get_permit_by_id(permit_id)
    if not permit:
        flash('Permit record not found!', 'danger')
        return redirect(url_for('permit.list_permits'))

    if request.method == 'POST':
        try:
            data = {
                'expiry_date': form_date(request.form, 'expiry_date'),
                'cost': form_float(request.form, 'cost'),
                'document_image': ''
            }
            
            PermitModel.update_permit(permit_id, data)
            flash('Permit renewed successfully!', 'success')
            return redirect(url_for('permit.list_permits'))
        except Exception as e:
            flash(f'Error renewing permit: {str(e)}', 'danger')
            return redirect(url_for('permit.renew_permit', permit_id=permit_id))
    
    return render_template('permits/renew.html', permit=permit, today=datetime.now().strftime('%Y-%m-%d'))

@permit_bp.route('/delete/<int:permit_id>')
@login_required
def delete_permit(permit_id):
    try:
        permit = PermitModel.get_permit_by_id(permit_id)
        if not permit:
            flash('Permit record not found!', 'danger')
        else:
            PermitModel.delete_permit(permit_id)
            flash('Permit record deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting permit: {str(e)}', 'danger')
    return redirect(url_for('permit.list_permits'))

@permit_bp.route('/expiring')
@login_required
def expiring_permits():
    days = request.args.get('days', 15, type=int)
    permits = PermitModel.get_expiring_permits(days)
    return render_template('permits/expiring.html', permits=permits, days=days)