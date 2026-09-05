from flask import Blueprint, render_template, request, redirect, url_for, flash, session, make_response
from functools import wraps
from models.vehicle_model import VehicleModel
from models.fuel_model import FuelModel
from models.maintenance_model import MaintenanceModel
from models.expense_model import ExpenseModel
from models.driver_model import DriverModel
from datetime import datetime
from database.db_manager import get_db_connection
import pandas as pd
from io import BytesIO

report_bp = Blueprint('report', __name__, url_prefix='/reports')

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('auth_login'))
        return f(*args, **kwargs)
    return decorated_function


@report_bp.route('/vehicle-stock')
@login_required
def vehicle_stock_report():
    """Vehicle Times Stock Report"""
    vehicles = VehicleModel.get_all_vehicles()
    stock_data = []
    
    for vehicle in vehicles:
        # Get fuel consumption data
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get last fuel entry
        cursor.execute('''
            SELECT liters, odometer_reading, date FROM fuel_consumption 
            WHERE vehicle_id = ? ORDER BY date DESC LIMIT 1
        ''', (vehicle['vehicle_id'],))
        last_fuel = cursor.fetchone()
        
        # Get last maintenance
        cursor.execute('''
            SELECT maintenance_type, date, next_due_km, next_due_date FROM maintenance 
            WHERE vehicle_id = ? ORDER BY date DESC LIMIT 1
        ''', (vehicle['vehicle_id'],))
        last_maintenance = cursor.fetchone()
        
        # Get last tuning
        cursor.execute('''
            SELECT date FROM tuning 
            WHERE vehicle_id = ? ORDER BY date DESC LIMIT 1
        ''', (vehicle['vehicle_id'],))
        last_tuning = cursor.fetchone()
        
        conn.close()
        
        stock_data.append({
            'vehicle_id': vehicle['vehicle_id'],
            'registration_no': vehicle['registration_no'],
            'make': vehicle['make'],
            'model': vehicle['model'],
            'fuel_in_tank': last_fuel['liters'] if last_fuel else 'N/A',
            'last_fuel_date': last_fuel['date'] if last_fuel else 'N/A',
            'last_odometer': last_fuel['odometer_reading'] if last_fuel else vehicle['current_odometer'],
            'last_maintenance': last_maintenance['maintenance_type'] if last_maintenance else 'None',
            'last_maintenance_date': last_maintenance['date'] if last_maintenance else 'N/A',
            'next_due_km': last_maintenance['next_due_km'] if last_maintenance else 'N/A',
            'next_due_date': last_maintenance['next_due_date'] if last_maintenance else 'N/A',
            'last_tuning': last_tuning['date'] if last_tuning else 'Not done'
        })
    
    return render_template('reports/vehicle_stock_report.html', stock_data=stock_data)


@report_bp.route('/expense-summary')
@login_required
def expense_summary():
    """Monthly expense summary by vehicle"""
    month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    vehicles = VehicleModel.get_all_vehicles()
    
    summary = []
    total_fuel = 0
    total_maintenance = 0
    total_parts = 0
    
    for vehicle in vehicles:
        # Get fuel cost for month
        fuel_cost = FuelModel.get_monthly_cost(vehicle['vehicle_id'], month)
        
        # Get maintenance cost for month
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT SUM(cost) as total FROM maintenance 
            WHERE vehicle_id = ? AND strftime('%Y-%m', date) = ?
        ''', (vehicle['vehicle_id'], month))
        maint_result = cursor.fetchone()
        maintenance_cost = maint_result['total'] if maint_result['total'] else 0
        
        # Get spare parts cost for month
        cursor.execute('''
            SELECT SUM(total_cost) as total FROM spare_parts_expense 
            WHERE vehicle_id = ? AND strftime('%Y-%m', date) = ?
        ''', (vehicle['vehicle_id'], month))
        parts_result = cursor.fetchone()
        parts_cost = parts_result['total'] if parts_result['total'] else 0
        
        conn.close()
        
        total_fuel += fuel_cost
        total_maintenance += maintenance_cost
        total_parts += parts_cost
        
        summary.append({
            'vehicle': f"{vehicle['registration_no']} - {vehicle['make']} {vehicle['model']}",
            'fuel_cost': fuel_cost,
            'maintenance_cost': maintenance_cost,
            'parts_cost': parts_cost,
            'total': fuel_cost + maintenance_cost + parts_cost
        })
    
    return render_template('reports/expense_summary.html', 
                         summary=summary, 
                         month=month,
                         total_fuel=total_fuel,
                         total_maintenance=total_maintenance,
                         total_parts=total_parts,
                         grand_total=total_fuel + total_maintenance + total_parts)


@report_bp.route('/export-excel')
@login_required
def export_excel():
    """Export vehicle stock report to Excel"""
    vehicles = VehicleModel.get_all_vehicles()
    data = []
    
    for vehicle in vehicles:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT liters, date FROM fuel_consumption 
            WHERE vehicle_id = ? ORDER BY date DESC LIMIT 1
        ''', (vehicle['vehicle_id'],))
        last_fuel = cursor.fetchone()
        
        cursor.execute('''
            SELECT maintenance_type, date FROM maintenance 
            WHERE vehicle_id = ? ORDER BY date DESC LIMIT 1
        ''', (vehicle['vehicle_id'],))
        last_maintenance = cursor.fetchone()
        
        conn.close()
        
        data.append({
            'Registration No': vehicle['registration_no'],
            'Make': vehicle['make'],
            'Model': vehicle['model'],
            'Last Fuel (Liters)': last_fuel['liters'] if last_fuel else '',
            'Last Fuel Date': last_fuel['date'] if last_fuel else '',
            'Last Maintenance': last_maintenance['maintenance_type'] if last_maintenance else '',
            'Last Maintenance Date': last_maintenance['date'] if last_maintenance else '',
            'Current Odometer (km)': vehicle['current_odometer'],
            'Status': vehicle['status']
        })
    
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Vehicle Stock Report', index=False)
    
    output.seek(0)
    return make_response(
        output.getvalue(),
        200,
        {
            'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'Content-Disposition': f'attachment; filename=vehicle_stock_{datetime.now().strftime("%Y%m%d")}.xlsx'
        }
    )