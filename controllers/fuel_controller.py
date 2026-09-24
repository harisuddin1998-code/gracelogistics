from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from functools import wraps
from models.fuel_model import FuelModel
from models.vehicle_model import VehicleModel
from datetime import datetime
from utils.helpers import form_text, form_float, form_int, form_date, form_id

fuel_bp = Blueprint('fuel', __name__, url_prefix='/fuel')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('auth_login'))
        return f(*args, **kwargs)
    return decorated_function

def _fuel_form_data():
    """Read the fuel form; blank/missing fields never raise."""
    return {
        'vehicle_id': form_id(request.form, 'vehicle_id'),
        'date': form_date(request.form, 'date'),
        'liters': form_float(request.form, 'liters'),
        'cost_per_liter': form_float(request.form, 'cost_per_liter'),
        'odometer_reading': form_int(request.form, 'odometer_reading'),
        'fuel_station': form_text(request.form, 'fuel_station')
    }


@fuel_bp.route('/entry', methods=['GET', 'POST'])
@login_required
def fuel_entry():
    if request.method == 'POST':
        try:
            data = _fuel_form_data()
            data['receipt_image'] = ''

            fuel_id = FuelModel.add_fuel_entry(data)
            
            # Check fuel efficiency alert
            efficiency = FuelModel.get_fuel_efficiency(data['vehicle_id'], 30)
            if efficiency < 8 and efficiency > 0:
                flash(f'Warning: Low fuel efficiency ({efficiency} km/l) for this vehicle!', 'warning')
            else:
                flash('Fuel entry added successfully!', 'success')
                
            return redirect(url_for('fuel.fuel_report'))
        except Exception as e:
            flash(f'Error adding fuel entry: {str(e)}', 'danger')
            return redirect(url_for('fuel.fuel_entry'))
    
    vehicles = VehicleModel.get_all_vehicles()
    return render_template('fuel/entry.html', vehicles=vehicles, today=datetime.now().strftime('%Y-%m-%d'))

@fuel_bp.route('/edit/<int:fuel_id>', methods=['GET', 'POST'])
@login_required
def edit_fuel(fuel_id):
    entry = FuelModel.get_fuel_entry_by_id(fuel_id)
    if not entry:
        flash('Fuel entry not found!', 'danger')
        return redirect(url_for('fuel.fuel_report'))
    
    if request.method == 'POST':
        try:
            data = _fuel_form_data()
            FuelModel.update_fuel_entry(fuel_id, data)
            flash('Fuel entry updated successfully!', 'success')
            return redirect(url_for('fuel.fuel_report'))
        except Exception as e:
            flash(f'Error updating fuel entry: {str(e)}', 'danger')
            return redirect(url_for('fuel.edit_fuel', fuel_id=fuel_id))
            
    vehicles = VehicleModel.get_all_vehicles()
    return render_template('fuel/edit.html', entry=entry, vehicles=vehicles)

@fuel_bp.route('/delete/<int:fuel_id>')
@login_required
def delete_fuel(fuel_id):
    try:
        entry = FuelModel.get_fuel_entry_by_id(fuel_id)
        if not entry:
            flash('Fuel entry not found!', 'danger')
        else:
            FuelModel.delete_fuel_entry(fuel_id)
            flash('Fuel entry deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting fuel entry: {str(e)}', 'danger')
    return redirect(url_for('fuel.fuel_report'))

@fuel_bp.route('/report')
@login_required
def fuel_report():
    vehicle_id = request.args.get('vehicle_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    entries = FuelModel.get_fuel_entries(vehicle_id, start_date, end_date)
    vehicles = VehicleModel.get_all_vehicles()
    
    # Calculate statistics
    total_cost = sum((entry['total_cost'] or 0) for entry in entries)
    total_liters = sum((entry['liters'] or 0) for entry in entries)
    avg_cost_per_liter = (total_cost / total_liters) if total_liters > 0 else 0
    
    return render_template('fuel/report.html', entries=entries, vehicles=vehicles, 
                         total_cost=total_cost, total_liters=total_liters,
                         avg_cost_per_liter=avg_cost_per_liter,
                         selected_vehicle=vehicle_id,
                         start_date=start_date, end_date=end_date)

@fuel_bp.route('/approve/<int:fuel_id>')
@login_required
def approve_fuel(fuel_id):
    user_id = session.get('user_id', 1)
    FuelModel.approve_fuel_entry(fuel_id, user_id)
    flash('Fuel entry approved!', 'success')
    return redirect(url_for('fuel.fuel_report'))

@fuel_bp.route('/api/efficiency/<int:vehicle_id>')
@login_required
def api_efficiency(vehicle_id):
    efficiency = FuelModel.get_fuel_efficiency(vehicle_id, 30)
    return jsonify({'vehicle_id': vehicle_id, 'efficiency': efficiency})