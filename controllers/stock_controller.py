from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from functools import wraps
from models.stock_model import StockModel
from models.vehicle_model import VehicleModel
from datetime import datetime

stock_bp = Blueprint('stock', __name__, url_prefix='/stock')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('auth_login'))
        return f(*args, **kwargs)
    return decorated_function

@stock_bp.route('/update', methods=['GET', 'POST'])
@login_required
def update_stock():
    if request.method == 'POST':
        try:
            data = {
                'vehicle_id': request.form['vehicle_id'],
                'date': request.form['date'],
                'fuel_in_tank': float(request.form.get('fuel_in_tank', 0)) if request.form.get('fuel_in_tank') else None,
                'oil_level': request.form.get('oil_level', 'OK'),
                'air_filter_status': request.form.get('air_filter_status', 'OK'),
                'oil_filter_status': request.form.get('oil_filter_status', 'OK'),
                'notes': request.form.get('notes', '')
            }
            
            StockModel.update_vehicle_stock(data)
            
            # Alert if oil is low
            if data['oil_level'] in ['Low', 'Critical']:
                flash(f'Warning: Oil level is {data["oil_level"]}! Please check immediately.', 'warning')
            else:
                flash('Vehicle stock status updated successfully!', 'success')
            
            return redirect(url_for('stock.update_stock'))
        except Exception as e:
            flash(f'Error updating stock: {str(e)}', 'danger')
            return redirect(url_for('stock.update_stock'))
    
    vehicles = VehicleModel.get_all_vehicles()
    return render_template('stock/update.html', vehicles=vehicles, today=datetime.now().strftime('%Y-%m-%d'))

@stock_bp.route('/alerts')
@login_required
def alerts():
    low_oil_vehicles = StockModel.get_low_oil_vehicles()
    return render_template('stock/alerts.html', low_oil_vehicles=low_oil_vehicles)

@stock_bp.route('/history/<int:vehicle_id>')
@login_required
def stock_history(vehicle_id):
    days = request.args.get('days', 30, type=int)
    history = StockModel.get_stock_history(vehicle_id, days)
    vehicle = VehicleModel.get_vehicle_by_id(vehicle_id)
    
    if not vehicle:
        flash('Vehicle not found!', 'danger')
        return redirect(url_for('stock.alerts'))
        
    return render_template('stock/history.html', history=history, vehicle=vehicle, days=days)

@stock_bp.route('/api/current')
@login_required
def api_current_stock():
    vehicles = VehicleModel.get_all_vehicles()
    stock_data = []
    
    for vehicle in vehicles:
        latest = StockModel.get_latest_stock(vehicle['vehicle_id'])
        if latest:
            stock_data.append({
                'vehicle_id': vehicle['vehicle_id'],
                'registration_no': vehicle['registration_no'],
                'fuel_in_tank': latest['fuel_in_tank'],
                'oil_level': latest['oil_level'],
                'last_update': latest['date']
            })
    
    return jsonify(stock_data)