from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from functools import wraps
from models.vehicle_model import VehicleModel
from models.driver_model import DriverModel

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

@vehicle_bp.route('/')
@login_required
def list_vehicles():
    vehicles = VehicleModel.get_all_vehicles()
    return render_template('vehicles/list.html', vehicles=vehicles)

@vehicle_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_vehicle():
    if request.method == 'POST':
        try:
            data = {
                'registration_no': request.form['registration_no'].strip().upper(),
                'make': request.form['make'].strip(),
                'model': request.form['model'].strip(),
                'year': request.form.get('year') or None,
                'engine_no': request.form.get('engine_no', '').strip(),
                'chassis_no': request.form.get('chassis_no', '').strip(),
                'purchase_date': request.form.get('purchase_date') or None,
                'purchase_cost': float(request.form['purchase_cost']) if request.form.get('purchase_cost') else 0,
                'current_odometer': int(request.form['current_odometer']) if request.form.get('current_odometer') else 0,
                'fuel_type': request.form['fuel_type'],
                'status': request.form['status'],
                'assigned_driver_id': int(request.form['assigned_driver_id']) if request.form.get('assigned_driver_id') else None
            }
            
            vehicle_id = VehicleModel.add_vehicle(data)
            flash(f'Vehicle {data["registration_no"]} added successfully!', 'success')
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
            data = {
                'registration_no': request.form['registration_no'].strip().upper(),
                'make': request.form['make'].strip(),
                'model': request.form['model'].strip(),
                'year': request.form.get('year') or None,
                'engine_no': request.form.get('engine_no', '').strip(),
                'chassis_no': request.form.get('chassis_no', '').strip(),
                'purchase_date': request.form.get('purchase_date') or None,
                'purchase_cost': float(request.form['purchase_cost']) if request.form.get('purchase_cost') else 0,
                'current_odometer': int(request.form['current_odometer']) if request.form.get('current_odometer') else 0,
                'fuel_type': request.form['fuel_type'],
                'status': request.form['status'],
                'assigned_driver_id': int(request.form['assigned_driver_id']) if request.form.get('assigned_driver_id') else None
            }
            
            VehicleModel.update_vehicle(vehicle_id, data)
            flash(f'Vehicle {data["registration_no"]} updated successfully!', 'success')
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
        
        registration = vehicle['registration_no']
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