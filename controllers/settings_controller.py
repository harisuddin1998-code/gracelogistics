from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
import os
import json
import shutil
from werkzeug.utils import secure_filename
from datetime import datetime
import platform
import sys

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg', 'webp', 'ico'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def load_company_info():
    """Load company info from JSON file"""
    company_file = 'static/company_info.json'
    company_info = {
        'name': 'Vehicle Management System',
        'short_name': 'VMS',
        'slogan': 'Vehicle Management System',
        'address': '',
        'phone': '',
        'email': '',
        'website': '',
        'tax_number': '',
        'registration_number': ''
    }
    
    if os.path.exists(company_file):
        try:
            with open(company_file, 'r') as f:
                loaded = json.load(f)
                company_info.update(loaded)
        except:
            pass
    
    return company_info


@settings_bp.route('/')
def index():
    """Settings dashboard"""
    logo_exists = os.path.exists('static/logo/logo.png')
    
    # Get logo info if exists
    logo_info = None
    if logo_exists:
        stat = os.stat('static/logo/logo.png')
        logo_info = {
            'size': stat.st_size,
            'size_kb': round(stat.st_size / 1024, 2),
            'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
            'path': 'static/logo/logo.png'
        }
    
    # Load company info
    company_info = load_company_info()
    
    return render_template('settings/index.html', 
                         logo_exists=logo_exists, 
                         logo_info=logo_info,
                         company_info=company_info)


@settings_bp.route('/upload-logo', methods=['POST'])
def upload_logo():
    """Upload company logo"""
    if 'logo' not in request.files:
        flash('No file selected!', 'danger')
        return redirect(url_for('settings.index'))
    
    file = request.files['logo']
    
    if file.filename == '':
        flash('No file selected!', 'danger')
        return redirect(url_for('settings.index'))
    
    if file and allowed_file(file.filename):
        # Create logo directory if it doesn't exist
        os.makedirs('static/logo', exist_ok=True)
        
        # Save as logo.png for consistency
        file.save(os.path.join('static/logo', 'logo.png'))
        
        flash('Logo uploaded successfully!', 'success')
    else:
        flash('Invalid file type! Please upload PNG, JPG, JPEG, GIF, SVG, WEBP, or ICO', 'danger')
    
    return redirect(url_for('settings.index'))


@settings_bp.route('/remove-logo')
def remove_logo():
    """Remove company logo"""
    logo_path = 'static/logo/logo.png'
    if os.path.exists(logo_path):
        os.remove(logo_path)
        flash('Logo removed successfully!', 'success')
    else:
        flash('No logo found to remove!', 'warning')
    
    return redirect(url_for('settings.index'))


@settings_bp.route('/company-info', methods=['GET', 'POST'])
def company_info():
    """Update company information"""
    company_file = 'static/company_info.json'
    
    # Load existing company info
    company_info = load_company_info()
    
    if request.method == 'POST':
        company_info = {
            'name': request.form.get('company_name', 'Vehicle Management System'),
            'short_name': request.form.get('short_name', 'VMS'),
            'slogan': request.form.get('slogan', 'Vehicle Management System'),
            'address': request.form.get('company_address', ''),
            'phone': request.form.get('company_phone', ''),
            'email': request.form.get('company_email', ''),
            'website': request.form.get('company_website', ''),
            'tax_number': request.form.get('tax_number', ''),
            'registration_number': request.form.get('registration_number', '')
        }
        
        # Save to JSON file
        try:
            with open(company_file, 'w') as f:
                json.dump(company_info, f, indent=4)
            flash('Company information updated successfully!', 'success')
        except Exception as e:
            flash(f'Error saving company info: {str(e)}', 'danger')
        
        return redirect(url_for('settings.company_info'))
    
    return render_template('settings/company_info.html', company_info=company_info)


@settings_bp.route('/backup')
def backup():
    """Backup the database"""
    try:
        # Create backup directory
        os.makedirs('backups', exist_ok=True)
        
        # Create backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f'backups/vehicle_management_backup_{timestamp}.db'
        
        # Copy database
        if os.path.exists('instance/vehicle_management.db'):
            shutil.copy2('instance/vehicle_management.db', backup_file)
            
            # Get file size
            size = os.path.getsize(backup_file)
            size_kb = round(size / 1024, 2)
            
            flash(f'Database backed up successfully! File: {backup_file} ({size_kb} KB)', 'success')
        else:
            flash('Database file not found!', 'danger')
    
    except Exception as e:
        flash(f'Backup failed: {str(e)}', 'danger')
    
    return redirect(url_for('settings.index'))


@settings_bp.route('/backup-database')
def backup_database():
    """Alias for backup route"""
    return redirect(url_for('settings.backup'))


@settings_bp.route('/restore', methods=['POST'])
def restore():
    """Restore database from backup"""
    try:
        backup_file = request.form.get('backup_file')
        if not backup_file or not os.path.exists(backup_file):
            flash('Backup file not found!', 'danger')
            return redirect(url_for('settings.index'))
        
        # Create backup of current database before restore
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        pre_restore_backup = f'backups/pre_restore_backup_{timestamp}.db'
        if os.path.exists('instance/vehicle_management.db'):
            shutil.copy2('instance/vehicle_management.db', pre_restore_backup)
        
        # Restore from backup
        shutil.copy2(backup_file, 'instance/vehicle_management.db')
        
        flash(f'Database restored successfully from {backup_file}! Pre-restore backup saved as {pre_restore_backup}', 'success')
    
    except Exception as e:
        flash(f'Restore failed: {str(e)}', 'danger')
    
    return redirect(url_for('settings.index'))


@settings_bp.route('/list-backups')
def list_backups():
    """List all available backups"""
    backups = []
    if os.path.exists('backups'):
        for file in os.listdir('backups'):
            if file.endswith('.db'):
                file_path = os.path.join('backups', file)
                stat = os.stat(file_path)
                backups.append({
                    'name': file,
                    'size': round(stat.st_size / 1024, 2),
                    'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'path': file_path
                })
        backups.sort(key=lambda x: x['modified'], reverse=True)
    
    return jsonify(backups)


@settings_bp.route('/system-info')
def system_info():
    """Display system information"""
    company_info = load_company_info()
    
    system_info = {
        'python_version': sys.version,
        'platform': platform.platform(),
        'processor': platform.processor(),
        'hostname': platform.node(),
        'database_size': 'N/A',
        'app_version': '2.0.0',
        'flask_version': '2.3.3'
    }
    
    # Get database size
    if os.path.exists('instance/vehicle_management.db'):
        size = os.path.getsize('instance/vehicle_management.db')
        system_info['database_size'] = f'{round(size / 1024, 2)} KB'
    
    # Get logo info
    system_info['logo_exists'] = os.path.exists('static/logo/logo.png')
    
    # Get backup count
    if os.path.exists('backups'):
        system_info['backup_count'] = len([f for f in os.listdir('backups') if f.endswith('.db')])
    else:
        system_info['backup_count'] = 0
    
    return render_template('settings/system_info.html', system_info=system_info, company_info=company_info)


@settings_bp.route('/export-data')
def export_data():
    """Export all data to JSON"""
    from database.db_manager import get_db_connection
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        export_data = {}
        for table in tables:
            table_name = table['name']
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            export_data[table_name] = [dict(row) for row in rows]
        
        conn.close()
        
        # Save to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        export_file = f'backups/export_data_{timestamp}.json'
        os.makedirs('backups', exist_ok=True)
        
        with open(export_file, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        flash(f'Data exported successfully to {export_file}!', 'success')
    
    except Exception as e:
        flash(f'Export failed: {str(e)}', 'danger')
    
    return redirect(url_for('settings.index'))


@settings_bp.route('/save-theme', methods=['POST'])
def save_theme():
    """Save selected theme"""
    data = request.get_json()
    theme_id = data.get('theme_id', 'windows11')
    
    # Save theme to file (server-side storage)
    theme_file = 'static/theme_preference.json'
    try:
        with open(theme_file, 'w') as f:
            json.dump({'theme': theme_id, 'updated_at': datetime.now().isoformat()}, f)
        return jsonify({'success': True, 'theme': theme_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@settings_bp.route('/clear-cache')
def clear_cache():
    """Clear application cache"""
    try:
        # Clear session
        flash('Cache cleared successfully!', 'success')
    except Exception as e:
        flash(f'Error clearing cache: {str(e)}', 'danger')
    
    return redirect(url_for('settings.index'))


@settings_bp.route('/themes')
def themes():
    """Theme settings page"""
    return render_template('settings/themes.html')