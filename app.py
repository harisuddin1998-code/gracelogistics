from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response
from database.db_manager import init_database, get_db_connection
from models.user_model import UserModel
import os
import json
from functools import wraps
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
app.config.from_object('config.Config')

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('instance', exist_ok=True)
os.makedirs('static/logo', exist_ok=True)
os.makedirs('backups', exist_ok=True)

# Initialize database on first run
if not os.path.exists('instance/vehicle_management.db'):
    init_database()

# ============================================
# CREATE MISSING MAINTENANCE TABLES (if needed)
# ============================================
def create_maintenance_tables():
    """Create the new unified maintenance tables if they do not exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if the 'maintenance' table already exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='maintenance'")
    if not cursor.fetchone():
        # Execute the full schema provided by user
        cursor.executescript('''
            -- MAINTENANCE TABLE (routine jobs)
            CREATE TABLE IF NOT EXISTS maintenance (
                maintenance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER NOT NULL,
                maintenance_type TEXT NOT NULL,
                date DATE NOT NULL,
                cost DECIMAL(10,2),
                quantity INTEGER DEFAULT 1,
                unit_price DECIMAL(10,2),
                next_due_km INTEGER,
                next_due_date DATE,
                mechanic_name TEXT,
                notes TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id),
                FOREIGN KEY (created_by) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS tuning (
                tuning_id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER NOT NULL,
                date DATE NOT NULL,
                tuning_type TEXT,
                cost DECIMAL(10,2),
                technician_name TEXT,
                before_performance TEXT,
                after_performance TEXT,
                notes TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id),
                FOREIGN KEY (created_by) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS electrical_work (
                electrical_id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER NOT NULL,
                date DATE NOT NULL,
                work_type TEXT,
                cost DECIMAL(10,2),
                technician_name TEXT,
                parts_used TEXT,
                hours_spent DECIMAL(4,2),
                notes TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id),
                FOREIGN KEY (created_by) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS body_work (
                body_work_id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER NOT NULL,
                date DATE NOT NULL,
                work_type TEXT,
                cost DECIMAL(10,2),
                workshop_name TEXT,
                painter_name TEXT,
                color_code TEXT,
                panels_repaired TEXT,
                warranty_months INTEGER DEFAULT 6,
                notes TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id),
                FOREIGN KEY (created_by) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS tire_change (
                tire_id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER NOT NULL,
                date DATE NOT NULL,
                tire_position TEXT,
                tire_brand TEXT,
                tire_size TEXT,
                quantity INTEGER DEFAULT 1,
                cost_per_tire DECIMAL(10,2),
                total_cost DECIMAL(10,2),
                alignment_done INTEGER DEFAULT 0,
                balancing_done INTEGER DEFAULT 0,
                old_tire_condition TEXT,
                next_rotation_km INTEGER,
                workshop_name TEXT,
                notes TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id),
                FOREIGN KEY (created_by) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS maintenance_schedule (
                schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER NOT NULL,
                maintenance_type TEXT NOT NULL,
                scheduled_date DATE,
                scheduled_km INTEGER,
                status TEXT DEFAULT 'Pending',
                assigned_to INTEGER,
                completed_date DATE,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id),
                FOREIGN KEY (assigned_to) REFERENCES users(user_id)
            );

            CREATE INDEX IF NOT EXISTS idx_maintenance_vehicle ON maintenance(vehicle_id);
            CREATE INDEX IF NOT EXISTS idx_maintenance_date ON maintenance(date);
            CREATE INDEX IF NOT EXISTS idx_tuning_vehicle ON tuning(vehicle_id);
            CREATE INDEX IF NOT EXISTS idx_electrical_vehicle ON electrical_work(vehicle_id);
            CREATE INDEX IF NOT EXISTS idx_body_vehicle ON body_work(vehicle_id);
            CREATE INDEX IF NOT EXISTS idx_tire_vehicle ON tire_change(vehicle_id);
            CREATE INDEX IF NOT EXISTS idx_schedule_vehicle ON maintenance_schedule(vehicle_id);
        ''')
        conn.commit()
        print("Maintenance tables created successfully.")
    conn.close()

# Call the function to ensure all maintenance tables exist
create_maintenance_tables()

# ============================================
# AUTHENTICATION DECORATOR
# ============================================

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

# ============================================
# CONTEXT PROCESSORS
# ============================================

@app.context_processor
def inject_global_variables():
    logo_exists = os.path.exists('static/logo/logo.png')
    company_file = 'static/company_info.json'
    company_info = {}
    if os.path.exists(company_file):
        try:
            with open(company_file, 'r') as f:
                company_info = json.load(f)
        except:
            company_info = {}
    
    if not company_info:
        company_info = {
            'name': app.config.get('APP_NAME', 'FleetMaster ERP'),
            'slogan': app.config.get('COMPANY_SLOGAN', 'Vehicle Management System'),
        }
    
    return dict(
        logo_exists=logo_exists,
        company_info=company_info,
        app_name=company_info.get('name', app.config.get('APP_NAME', 'FME')),
        current_year=datetime.now().year,
        user_logged_in='user_id' in session,
        user_name=session.get('user_name', ''),
        user_role=session.get('role', '')
    )

# ============================================
# AUTHENTICATION ROUTES
# ============================================

@app.route('/login', methods=['GET', 'POST'])
def auth_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = UserModel.authenticate(username, password)
        if user:
            session['user_id'] = user['user_id']
            session['user_name'] = user['full_name']
            session['username'] = user['username']
            session['role'] = user['role']
            
            flash(f'Welcome back, {user["full_name"]}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('auth/login.html')

@app.route('/logout')
def auth_logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth_login'))

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'danger')
            return redirect(url_for('change_password'))
        
        user = UserModel.authenticate(session['username'], current_password)
        if user:
            UserModel.change_password(session['user_id'], new_password)
            flash('Password changed successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Current password is incorrect', 'danger')
    
    return render_template('auth/change_password.html')

# ============================================
# MAIN ROUTES
# ============================================

@app.route('/')
@login_required
def index():
    from models.vehicle_model import VehicleModel
    from models.driver_model import DriverModel
    from models.fuel_model import FuelModel
    from models.permit_model import PermitModel
    from models.expense_model import ExpenseModel
    
    vehicle_stats = VehicleModel.get_vehicle_stats()
    driver_stats = DriverModel.get_driver_stats()
    recent_fuel = FuelModel.get_fuel_entries(limit=5)
    drivers = DriverModel.get_all_drivers()
    drivers_with_advance = [d for d in drivers if d['advance_balance'] and d['advance_balance'] > 0]
    expiring_permits = PermitModel.get_expiring_permits(30)
    low_stock = ExpenseModel.get_low_stock_items()
    
    return render_template('dashboard/admin_dashboard.html', 
                         vehicle_stats=vehicle_stats,
                         driver_stats=driver_stats,
                         recent_fuel=recent_fuel,
                         drivers_with_advance=drivers_with_advance,
                         expiring_permits=expiring_permits,
                         low_stock=low_stock)

# ============================================
# IMPORT ALL CONTROLLERS
# ============================================

from controllers.vehicle_controller import vehicle_bp
from controllers.driver_controller import driver_bp
from controllers.fuel_controller import fuel_bp
from controllers.maintenance_controller import maintenance_bp
from controllers.expense_controller import expense_bp
from controllers.salary_controller import salary_bp
from controllers.permit_controller import permit_bp
from controllers.stock_controller import stock_bp
from controllers.report_controller import report_bp
from controllers.settings_controller import settings_bp
from controllers.vendor_controller import vendor_bp

app.register_blueprint(vehicle_bp)
app.register_blueprint(driver_bp)
app.register_blueprint(fuel_bp)
app.register_blueprint(maintenance_bp)
app.register_blueprint(expense_bp)
app.register_blueprint(salary_bp)
app.register_blueprint(permit_bp)
app.register_blueprint(stock_bp)
app.register_blueprint(report_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(vendor_bp)

# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500

# ============================================
# MAIN ENTRY POINT
# ============================================

if __name__ == '__main__':
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5001))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    print("=" * 60)
    print(f"Starting {app.config.get('APP_NAME', 'FleetMaster ERP')}")
    print("=" * 60)
    print(f"Server: http://{host}:{port}")
    print(f"Login: admin / admin123")
    print("=" * 60)
    
    app.run(debug=debug, host=host, port=port)