from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
from datetime import datetime
from models.attendance_model import AttendanceModel, ATTENDANCE_CODES, attendance_code
from models.vehicle_model import VehicleModel
from utils.helpers import form_text

attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')

CODE_LABELS = {
    'present': 'Present',
    'garage': 'Absent - In Garage',
    'driver_absent': 'Absent - Driver Absent',
    'no_driver': 'Absent - No Driver Assigned',
}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('auth_login'))
        return f(*args, **kwargs)
    return decorated_function


def _valid_date(value):
    try:
        return datetime.strptime(value, '%Y-%m-%d').strftime('%Y-%m-%d')
    except (TypeError, ValueError):
        return datetime.now().strftime('%Y-%m-%d')


def _valid_month(value):
    try:
        return datetime.strptime(value, '%Y-%m').strftime('%Y-%m')
    except (TypeError, ValueError):
        return datetime.now().strftime('%Y-%m')


def _allowed_codes(vehicle):
    """A car with a driver can be present, in garage or missing its driver;
    a car with no driver can only be absent (no driver) or in garage."""
    if vehicle['assigned_driver_id']:
        return ['present', 'garage', 'driver_absent']
    return ['no_driver', 'garage']


def _default_code(vehicle):
    if not vehicle['assigned_driver_id']:
        return 'no_driver'
    if vehicle['status'] == 'Under Repair':
        return 'garage'
    return 'present'


def _active_vehicles():
    return [v for v in VehicleModel.get_all_vehicles() if v['status'] != 'Retired']


@attendance_bp.route('/', methods=['GET', 'POST'])
@login_required
def mark_attendance():
    date = _valid_date(request.values.get('date'))
    vehicles = _active_vehicles()

    if request.method == 'POST':
        entries = []
        for vehicle in vehicles:
            vid = vehicle['vehicle_id']
            code = request.form.get(f'code_{vid}')
            if code not in _allowed_codes(vehicle):
                code = _default_code(vehicle)
            entries.append({
                'vehicle_id': vid,
                'driver_id': vehicle['assigned_driver_id'],
                'code': code,
                'notes': form_text(request.form, f'notes_{vid}'),
            })
        try:
            AttendanceModel.save_day(date, entries, session.get('user_id'))
            flash(f'Attendance saved for {date} ({len(entries)} vehicles).', 'success')
        except Exception as e:
            flash(f'Error saving attendance: {str(e)}', 'danger')
        return redirect(url_for('attendance.mark_attendance', date=date))

    saved = AttendanceModel.get_day(date)
    rows = []
    for vehicle in vehicles:
        record = saved.get(vehicle['vehicle_id'])
        code = attendance_code(record) if record else _default_code(vehicle)
        if code not in _allowed_codes(vehicle):
            # the driver was assigned/removed after this day was saved; show the stored value anyway
            allowed = _allowed_codes(vehicle) + [code]
        else:
            allowed = _allowed_codes(vehicle)
        rows.append({
            'vehicle': vehicle,
            'code': code,
            'allowed': allowed,
            'notes': record['notes'] if record else '',
            'saved': record is not None,
        })

    counts = {key: sum(1 for r in rows if r['code'] == key) for key in ATTENDANCE_CODES}
    return render_template('attendance/mark.html', rows=rows, date=date, counts=counts,
                           is_saved=bool(saved), labels=CODE_LABELS)


@attendance_bp.route('/report')
@login_required
def attendance_report():
    month = _valid_month(request.args.get('month'))
    vehicles = AttendanceModel.get_vehicle_month_summary(month)
    drivers = []
    for d in AttendanceModel.get_driver_month_summary(month):
        dates = sorted((d['absent_dates'] or '').split(',')) if d['absent_dates'] else []
        drivers.append({**dict(d), 'absent_dates': ', '.join(x.lstrip('0') for x in dates)})

    totals = {
        'present': sum(v['present_days'] for v in vehicles),
        'garage': sum(v['garage_days'] for v in vehicles),
        'driver_absent': sum(v['driver_absent_days'] for v in vehicles),
        'no_driver': sum(v['no_driver_days'] for v in vehicles),
    }
    return render_template('attendance/report.html', month=month, vehicles=vehicles,
                           drivers=drivers, totals=totals)
