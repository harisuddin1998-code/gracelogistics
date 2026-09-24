from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from functools import wraps
from models.vendor_model import VendorModel
from models.expense_model import ExpenseModel
from utils.helpers import form_text, form_int

vendor_bp = Blueprint('vendor', __name__, url_prefix='/vendors')

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('auth_login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('auth_login'))
        if session.get('role') != 'admin':
            flash('Admin access required', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def _vendor_form_data():
    """Read the vendor form; blank/missing fields never raise."""
    return {
        'vendor_name': form_text(request.form, 'vendor_name'),
        'contact_person': form_text(request.form, 'contact_person'),
        'phone': form_text(request.form, 'phone'),
        'email': form_text(request.form, 'email'),
        'address': form_text(request.form, 'address'),
        'tax_number': form_text(request.form, 'tax_number'),
        'payment_terms': form_text(request.form, 'payment_terms'),
        'rating': form_int(request.form, 'rating', 3)
    }


@vendor_bp.route('/')
@login_required
def list_vendors():
    vendors = VendorModel.get_all_vendors()
    return render_template('vendors/list.html', vendors=vendors)

@vendor_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_vendor():
    if request.method == 'POST':
        data = _vendor_form_data()
        
        vendor_id = VendorModel.add_vendor(data)
        flash(f'Vendor {data["vendor_name"] or "record"} added successfully!', 'success')
        return redirect(url_for('vendor.list_vendors'))
    
    return render_template('vendors/add.html')

@vendor_bp.route('/edit/<int:vendor_id>', methods=['GET', 'POST'])
@login_required
def edit_vendor(vendor_id):
    vendor = VendorModel.get_vendor_by_id(vendor_id)
    if not vendor:
        flash('Vendor not found!', 'danger')
        return redirect(url_for('vendor.list_vendors'))
    
    if request.method == 'POST':
        data = _vendor_form_data()
        data['is_active'] = 1 if request.form.get('is_active') == 'on' else 0
        
        VendorModel.update_vendor(vendor_id, data)
        flash(f'Vendor updated successfully!', 'success')
        return redirect(url_for('vendor.list_vendors'))
    
    return render_template('vendors/edit.html', vendor=vendor)

@vendor_bp.route('/delete/<int:vendor_id>')
@admin_required
def delete_vendor(vendor_id):
    try:
        VendorModel.delete_vendor(vendor_id)
        flash('Vendor deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting vendor: {str(e)}', 'danger')
    return redirect(url_for('vendor.list_vendors'))

@vendor_bp.route('/api/stats')
@login_required
def api_vendor_stats():
    stats = VendorModel.get_vendor_stats()
    return jsonify(stats)