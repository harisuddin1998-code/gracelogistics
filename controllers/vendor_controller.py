from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from functools import wraps
from models.vendor_model import VendorModel
from models.expense_model import ExpenseModel

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

@vendor_bp.route('/')
@login_required
def list_vendors():
    vendors = VendorModel.get_all_vendors()
    return render_template('vendors/list.html', vendors=vendors)

@vendor_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_vendor():
    if request.method == 'POST':
        data = {
            'vendor_name': request.form['vendor_name'],
            'contact_person': request.form.get('contact_person', ''),
            'phone': request.form.get('phone', ''),
            'email': request.form.get('email', ''),
            'address': request.form.get('address', ''),
            'tax_number': request.form.get('tax_number', ''),
            'payment_terms': request.form.get('payment_terms', ''),
            'rating': int(request.form.get('rating', 3))
        }
        
        vendor_id = VendorModel.add_vendor(data)
        flash(f'Vendor {data["vendor_name"]} added successfully!', 'success')
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
        data = {
            'vendor_name': request.form['vendor_name'],
            'contact_person': request.form.get('contact_person', ''),
            'phone': request.form.get('phone', ''),
            'email': request.form.get('email', ''),
            'address': request.form.get('address', ''),
            'tax_number': request.form.get('tax_number', ''),
            'payment_terms': request.form.get('payment_terms', ''),
            'rating': int(request.form.get('rating', 3)),
            'is_active': 1 if request.form.get('is_active') == 'on' else 0
        }
        
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