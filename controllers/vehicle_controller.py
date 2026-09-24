from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from functools import wraps
from models.vehicle_model import VehicleModel
from models.driver_model import DriverModel
from utils.helpers import (form_text, form_text_or_none, form_int_or_none, form_int,
                           form_float, form_date, form_id)

vehicle_bp = Blueprint('vehicle', __name__, url_prefix='/vehicles')

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('auth_login'))
        return f(*args, **kwargs)
    return decorated_function

def _vehicle_form_data():
    """Read the vehicle form; blank/missing fields never raise."""
    registration_no = form_text_or_none(request.form, 'registration_no')
    return {
        # NULL (not '') when blank so several vehicles can be saved without a plate number
        'registration_no': registration_no.upper() if registration_no else None,
        'make': form_text(request.form, 'make'),
        'model': form_text(request.form, 'model'),
        'year': form_int_or_none(request.form, 'year'),
        'engine_no': form_text(request.form, 'engine_no'),
        'chassis_no': form_text(request.form, 'chassis_no'),
        'purchase_date': form_date(request.form, 'purchase_date'),
        'purchase_cost': form_float(request.form, 'purchase_cost'),
        'current_odometer': form_int(request.form, 'current_odometer'),
        'fuel_type': form_text_or_none(request.form, 'fuel_type'),
        'status': form_text(request.form, 'status', 'Active'),
        'assigned_driver_id': form_id(request.form, 'assigned_driver_id')
    }


# Filters behind the clickable boxes on the vehicle list: ?filter=<key>
VEHICLE_FILTERS = {
    'active': ('Operational vehicles', lambda v: v['status'] == 'Active'),
    'repair': ('Vehicles under maintenance', lambda v: v['status'] == 'Under Repair'),
    'retired': ('Retired vehicles', lambda v: v['status'] == 'Retired'),
    'unassigned': ('Vehicles without a driver', lambda v: not v['assigned_driver_id']),
}


@vehicle_bp.route('/')
@login_required
def list_vehicles():
    all_vehicles = VehicleModel.get_all_vehicles()

    active_filter = request.args.get('filter', '')
    vehicles, filter_label = all_vehicles, None
    if active_filter in VEHICLE_FILTERS:
        filter_label, keep = VEHICLE_FILTERS[active_filter]
        vehicles = [v for v in all_vehicles if keep(v)]
    else:
        active_filter = ''

    # box counts always describe the whole fleet, not the filtered rows
    stats = {
        'total': len(all_vehicles),
        'active': sum(1 for v in all_vehicles if v['status'] == 'Active'),
        'repair': sum(1 for v in all_vehicles if v['status'] == 'Under Repair'),
        'unassigned': sum(1 for v in all_vehicles if not v['assigned_driver_id']),
    }
    return render_template('vehicles/list.html', vehicles=vehicles, stats=stats,
                           active_filter=active_filter, filter_label=filter_label)

@vehicle_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_vehicle():
    if request.method == 'POST':
        try:
            data = _vehicle_form_data()
            
            vehicle_id = VehicleModel.add_vehicle(data)
            flash(f'Vehicle {data["registration_no"] or "record"} added successfully!', 'success')
            return redirect(url_for('vehicle.list_vehicles'))
            
        except Exception as e:
            flash(f'Error adding vehicle: {str(e)}', 'danger')
            return redirect(url_for('vehicle.add_vehicle'))
    
    drivers = DriverModel.get_all_drivers()
    return render_template('vehicles/add.html', drivers=drivers)

@vehicle_bp.route('/edit/<int:vehicle_id>', methods=['GET', 'POST'])
@login_required
def edit_vehicle(vehicle_id):
    vehicle = VehicleModel.get_vehicle_by_id(vehicle_id)
    
    if not vehicle:
        flash('Vehicle not found!', 'danger')
        return redirect(url_for('vehicle.list_vehicles'))
    
    if request.method == 'POST':
        try:
            data = _vehicle_form_data()
            
            VehicleModel.update_vehicle(vehicle_id, data)
            flash(f'Vehicle {data["registration_no"] or "record"} updated successfully!', 'success')
            return redirect(url_for('vehicle.list_vehicles'))
            
        except Exception as e:
            flash(f'Error updating vehicle: {str(e)}', 'danger')
            return redirect(url_for('vehicle.edit_vehicle', vehicle_id=vehicle_id))
    
    drivers = DriverModel.get_all_drivers()
    return render_template('vehicles/edit.html', vehicle=vehicle, drivers=drivers)

@vehicle_bp.route('/delete/<int:vehicle_id>')
@login_required
def delete_vehicle(vehicle_id):
    try:
        vehicle = VehicleModel.get_vehicle_by_id(vehicle_id)
        if not vehicle:
            flash('Vehicle not found!', 'danger')
            return redirect(url_for('vehicle.list_vehicles'))
        
        registration = vehicle['registration_no'] or 'record'
        VehicleModel.delete_vehicle(vehicle_id)
        flash(f'Vehicle {registration} deleted successfully!', 'success')
        
    except Exception as e:
        flash(f'Error deleting vehicle: {str(e)}', 'danger')
    
    return redirect(url_for('vehicle.list_vehicles'))

@vehicle_bp.route('/api/stats')
@login_required
def api_vehicle_stats():
    stats = VehicleModel.get_vehicle_stats()
    return jsonify(stats)