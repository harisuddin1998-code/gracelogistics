from flask import Blueprint, render_template, request, redirect, url_for, flash, session, make_response
from functools import wraps
from datetime import datetime
from database.db_manager import get_db_connection
import io
import pandas as pd

maintenance_bp = Blueprint('maintenance', __name__, url_prefix='/maintenance')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first', 'warning')
            return redirect(url_for('auth_login'))
        return f(*args, **kwargs)
    return decorated_function

# ============================================================
# UNIFIED ADD MAINTENANCE RECORD
# ============================================================
@maintenance_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_maintenance():
    conn = get_db_connection()
    vehicles = conn.execute('SELECT vehicle_id, registration_no, make, model FROM vehicles ORDER BY registration_no').fetchall()
    conn.close()

    if request.method == 'POST':
        maintenance_type = request.form.get('maintenance_type')
        vehicle_id = request.form.get('vehicle_id')
        date = request.form.get('date')
        cost = float(request.form.get('cost') or 0)
        notes = request.form.get('notes', '')
        created_by = session.get('user_id')

        if not vehicle_id or not date:
            flash('Vehicle and Date are required', 'danger')
            return redirect(url_for('maintenance.add_maintenance'))

        conn = get_db_connection()
        try:
            # ----- ROUTINE MAINTENANCE (goes to `maintenance` table) -----
            if maintenance_type in ['oil_change', 'filter_change']:
                # Convert form type to the exact string expected by maintenance_type column
                type_map = {
                    'oil_change': 'Oil Change',
                    'filter_change': request.form.get('filter_type')  # e.g., Air Filter, Oil Filter etc.
                }
                maint_type = type_map.get(maintenance_type, '')
                if maintenance_type == 'filter_change':
                    maint_type = request.form.get('filter_type')
                
                quantity = int(request.form.get('quantity') or 1)
                unit_price = cost / quantity if quantity else cost
                next_due_km = request.form.get('next_due_km')
                next_due_date = request.form.get('next_due_date') or None
                mechanic_name = request.form.get('mechanic_name')

                conn.execute('''INSERT INTO maintenance 
                    (vehicle_id, maintenance_type, date, cost, quantity, unit_price, 
                     next_due_km, next_due_date, mechanic_name, notes, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (vehicle_id, maint_type, date, cost, quantity, unit_price,
                     next_due_km, next_due_date, mechanic_name, notes, created_by))

            # ----- TUNING -----
            elif maintenance_type == 'tuning':
                tuning_type = request.form.get('tuning_type')
                technician_name = request.form.get('technician_name')
                before_performance = request.form.get('before_performance')
                after_performance = request.form.get('after_performance')

                conn.execute('''INSERT INTO tuning 
                    (vehicle_id, date, tuning_type, cost, technician_name, 
                     before_performance, after_performance, notes, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (vehicle_id, date, tuning_type, cost, technician_name,
                     before_performance, after_performance, notes, created_by))

            # ----- ELECTRICAL WORK -----
            elif maintenance_type == 'electrical':
                work_type = request.form.get('work_type')
                technician_name = request.form.get('technician_name')
                hours_spent = request.form.get('hours_spent')
                parts_used = request.form.get('parts_used')

                conn.execute('''INSERT INTO electrical_work 
                    (vehicle_id, date, work_type, cost, technician_name, parts_used, hours_spent, notes, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (vehicle_id, date, work_type, cost, technician_name, parts_used, hours_spent, notes, created_by))

            # ----- BODY WORK -----
            elif maintenance_type == 'body_work':
                work_type = request.form.get('work_type')
                workshop_name = request.form.get('workshop_name')
                painter_name = request.form.get('painter_name')
                color_code = request.form.get('color_code')
                panels_repaired = request.form.get('panels_repaired')
                warranty_months = request.form.get('warranty_months') or 6

                conn.execute('''INSERT INTO body_work 
                    (vehicle_id, date, work_type, cost, workshop_name, painter_name, 
                     color_code, panels_repaired, warranty_months, notes, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (vehicle_id, date, work_type, cost, workshop_name, painter_name,
                     color_code, panels_repaired, warranty_months, notes, created_by))

            # ----- TIRE CHANGE -----
            elif maintenance_type == 'tire_change':
                tire_position = request.form.get('tire_position')
                tire_brand = request.form.get('tire_brand')
                tire_size = request.form.get('tire_size')
                quantity = int(request.form.get('quantity') or 1)
                cost_per_tire = float(request.form.get('cost_per_tire') or 0)
                total_cost = cost  # already the total cost from form
                alignment_done = 1 if request.form.get('alignment_done') else 0
                balancing_done = 1 if request.form.get('balancing_done') else 0
                old_tire_condition = request.form.get('old_tire_condition')
                next_rotation_km = request.form.get('next_rotation_km')
                workshop_name = request.form.get('workshop_name')

                conn.execute('''INSERT INTO tire_change 
                    (vehicle_id, date, tire_position, tire_brand, tire_size, quantity, 
                     cost_per_tire, total_cost, alignment_done, balancing_done, 
                     old_tire_condition, next_rotation_km, workshop_name, notes, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (vehicle_id, date, tire_position, tire_brand, tire_size, quantity,
                     cost_per_tire, total_cost, alignment_done, balancing_done,
                     old_tire_condition, next_rotation_km, workshop_name, notes, created_by))

            else:
                flash('Invalid maintenance type', 'danger')
                return redirect(url_for('maintenance.add_maintenance'))

            conn.commit()
            flash(f'{maintenance_type.replace("_", " ").title()} record saved successfully!', 'success')

        except Exception as e:
            conn.rollback()
            flash(f'Database error: {str(e)}', 'danger')
        finally:
            conn.close()

        return redirect(url_for('maintenance.history'))

    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('maintenance/add.html', vehicles=vehicles, today=today)


# ============================================================
# HISTORY – SHOW ALL RECORDS FROM ALL TABLES
# ============================================================
@maintenance_bp.route('/history')
@login_required
def history():
    conn = get_db_connection()
    vehicles = conn.execute('SELECT vehicle_id, registration_no, make, model FROM vehicles ORDER BY registration_no').fetchall()
    selected_vehicle = request.args.get('vehicle_id', '')

    # Helper to build query with optional vehicle filter
    def fetch_records(table, base_query, type_label):
        query = base_query
        params = []
        if selected_vehicle:
            query += f" WHERE {table}.vehicle_id = ?"
            params.append(selected_vehicle)
        records = conn.execute(query, params).fetchall()
        return records

    # 1. Routine maintenance (maintenance table)
    maint_records = conn.execute('''
        SELECT m.*, v.registration_no, 'Maintenance' as category
        FROM maintenance m
        JOIN vehicles v ON m.vehicle_id = v.vehicle_id
        WHERE (? = '' OR m.vehicle_id = ?)
    ''', (selected_vehicle, selected_vehicle)).fetchall()

    # 2. Tuning
    tuning_records = conn.execute('''
        SELECT t.*, v.registration_no, 'Tuning' as category
        FROM tuning t
        JOIN vehicles v ON t.vehicle_id = v.vehicle_id
        WHERE (? = '' OR t.vehicle_id = ?)
    ''', (selected_vehicle, selected_vehicle)).fetchall()

    # 3. Electrical
    elec_records = conn.execute('''
        SELECT e.*, v.registration_no, 'Electrical' as category
        FROM electrical_work e
        JOIN vehicles v ON e.vehicle_id = v.vehicle_id
        WHERE (? = '' OR e.vehicle_id = ?)
    ''', (selected_vehicle, selected_vehicle)).fetchall()

    # 4. Body work
    body_records = conn.execute('''
        SELECT b.*, v.registration_no, 'Body Work' as category
        FROM body_work b
        JOIN vehicles v ON b.vehicle_id = v.vehicle_id
        WHERE (? = '' OR b.vehicle_id = ?)
    ''', (selected_vehicle, selected_vehicle)).fetchall()

    # 5. Tire change
    tire_records = conn.execute('''
        SELECT tr.*, v.registration_no, 'Tire Change' as category
        FROM tire_change tr
        JOIN vehicles v ON tr.vehicle_id = v.vehicle_id
        WHERE (? = '' OR tr.vehicle_id = ?)
    ''', (selected_vehicle, selected_vehicle)).fetchall()

    conn.close()

    # Combine all records, sort by date desc
    all_records = list(maint_records) + list(tuning_records) + list(elec_records) + list(body_records) + list(tire_records)
    all_records.sort(key=lambda x: x['date'], reverse=True)

    return render_template('maintenance/history.html', 
                           vehicles=vehicles, 
                           records=all_records,
                           selected_vehicle=selected_vehicle)


# ============================================================
# REPORT – COST SUMMARY BY MAINTENANCE TYPE
# ============================================================
@maintenance_bp.route('/report')
@login_required
def report():
    conn = get_db_connection()
    vehicles = conn.execute('SELECT vehicle_id, registration_no, make, model FROM vehicles ORDER BY registration_no').fetchall()
    selected_vehicle = request.args.get('vehicle_id', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    summary = []
    total_cost = 0

    def add_summary(name, data_list):
        nonlocal total_cost
        if data_list:
            cnt = len(data_list)
            total = sum(row['cost'] for row in data_list)
            avg = total / cnt
            first = min(row['date'] for row in data_list)
            last = max(row['date'] for row in data_list)
            summary.append({
                'maintenance_type': name,
                'total_count': cnt,
                'total_cost': total,
                'avg_cost': avg,
                'first_date': first,
                'last_date': last
            })
            total_cost += total

    # Build filters
    veh_filter = "" if not selected_vehicle else f"AND vehicle_id = {selected_vehicle}"
    date_filter = ""
    if start_date and end_date:
        date_filter = f"AND date BETWEEN '{start_date}' AND '{end_date}'"
    elif start_date:
        date_filter = f"AND date >= '{start_date}'"
    elif end_date:
        date_filter = f"AND date <= '{end_date}'"

    # 1. Maintenance table – group by maintenance_type
    maint_types = conn.execute(f'''
        SELECT maintenance_type, COUNT(*) as cnt, SUM(cost) as total, AVG(cost) as avg, MIN(date) as first, MAX(date) as last
        FROM maintenance WHERE 1=1 {veh_filter} {date_filter} GROUP BY maintenance_type
    ''').fetchall()
    for mt in maint_types:
        summary.append({
            'maintenance_type': mt['maintenance_type'],
            'total_count': mt['cnt'],
            'total_cost': mt['total'],
            'avg_cost': mt['avg'],
            'first_date': mt['first'],
            'last_date': mt['last']
        })
        total_cost += (mt['total'] or 0)

    # 2. Tuning
    tuning = conn.execute(f"SELECT * FROM tuning WHERE 1=1 {veh_filter} {date_filter}").fetchall()
    add_summary('Tuning', tuning)

    # 3. Electrical
    electrical = conn.execute(f"SELECT * FROM electrical_work WHERE 1=1 {veh_filter} {date_filter}").fetchall()
    add_summary('Electrical Work', electrical)

    # 4. Body Work
    body = conn.execute(f"SELECT * FROM body_work WHERE 1=1 {veh_filter} {date_filter}").fetchall()
    add_summary('Body Work', body)

    # 5. Tire Change
    tires = conn.execute(f"SELECT * FROM tire_change WHERE 1=1 {veh_filter} {date_filter}").fetchall()
    add_summary('Tire Change', tires)

    conn.close()
    summary.sort(key=lambda x: x['total_cost'], reverse=True)

    return render_template('maintenance/report.html', vehicles=vehicles, summary=summary, total_cost=total_cost,
                         selected_vehicle=selected_vehicle, start_date=start_date, end_date=end_date)


# ============================================================
# EXPORT TO EXCEL (UNIFIED)
# ============================================================
@maintenance_bp.route('/export_excel')
@login_required
def export_excel():
    vehicle_id = request.args.get('vehicle_id', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    conn = get_db_connection()
    veh_filter = f"AND vehicle_id = {vehicle_id}" if vehicle_id else ""
    date_filter = ""
    if start_date and end_date:
        date_filter = f"AND date BETWEEN '{start_date}' AND '{end_date}'"
    elif start_date:
        date_filter = f"AND date >= '{start_date}'"
    elif end_date:
        date_filter = f"AND date <= '{end_date}'"

    # Fetch from each table
    maint = conn.execute(f'''
        SELECT m.date, v.registration_no, 'Maintenance' as type, m.maintenance_type as sub_type, m.cost, m.quantity, m.mechanic_name, m.notes
        FROM maintenance m JOIN vehicles v ON m.vehicle_id = v.vehicle_id
        WHERE 1=1 {veh_filter} {date_filter}
    ''').fetchall()
    tuning = conn.execute(f'''
        SELECT t.date, v.registration_no, 'Tuning' as type, t.tuning_type as sub_type, t.cost, NULL as quantity, t.technician_name as mechanic_name, t.notes
        FROM tuning t JOIN vehicles v ON t.vehicle_id = v.vehicle_id
        WHERE 1=1 {veh_filter} {date_filter}
    ''').fetchall()
    electrical = conn.execute(f'''
        SELECT e.date, v.registration_no, 'Electrical' as type, e.work_type as sub_type, e.cost, NULL as quantity, e.technician_name as mechanic_name, e.notes
        FROM electrical_work e JOIN vehicles v ON e.vehicle_id = v.vehicle_id
        WHERE 1=1 {veh_filter} {date_filter}
    ''').fetchall()
    body = conn.execute(f'''
        SELECT b.date, v.registration_no, 'Body Work' as type, b.work_type as sub_type, b.cost, NULL as quantity, b.painter_name as mechanic_name, b.notes
        FROM body_work b JOIN vehicles v ON b.vehicle_id = v.vehicle_id
        WHERE 1=1 {veh_filter} {date_filter}
    ''').fetchall()
    tires = conn.execute(f'''
        SELECT tr.date, v.registration_no, 'Tire Change' as type, tr.tire_position as sub_type, tr.total_cost as cost, tr.quantity, tr.workshop_name as mechanic_name, tr.notes
        FROM tire_change tr JOIN vehicles v ON tr.vehicle_id = v.vehicle_id
        WHERE 1=1 {veh_filter} {date_filter}
    ''').fetchall()

    conn.close()

    all_data = []
    for row in maint: all_data.append(dict(row))
    for row in tuning: all_data.append(dict(row))
    for row in electrical: all_data.append(dict(row))
    for row in body: all_data.append(dict(row))
    for row in tires: all_data.append(dict(row))

    if not all_data:
        flash('No data to export', 'warning')
        return redirect(url_for('maintenance.report'))

    df = pd.DataFrame(all_data)
    df = df.sort_values('date', ascending=False)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Maintenance Records', index=False)

    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename=maintenance_export_{datetime.now().strftime("%Y%m%d")}.xlsx'
    response.headers['Content-type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    return response


# ============================================================
# SCHEDULE ROUTES (unchanged except table name)
# ============================================================
@maintenance_bp.route('/schedule', methods=['GET', 'POST'])
@login_required
def schedule():
    conn = get_db_connection()
    if request.method == 'POST':
        vehicle_id = request.form.get('vehicle_id')
        maintenance_type = request.form.get('maintenance_type')
        scheduled_date = request.form.get('scheduled_date') or None
        scheduled_km = request.form.get('scheduled_km') or None
        assigned_to = request.form.get('assigned_to')
        notes = request.form.get('notes')

        conn.execute('''INSERT INTO maintenance_schedule 
                        (vehicle_id, maintenance_type, scheduled_date, scheduled_km, assigned_to, notes, status)
                        VALUES (?, ?, ?, ?, ?, ?, 'Pending')''',
                     (vehicle_id, maintenance_type, scheduled_date, scheduled_km, assigned_to, notes))
        conn.commit()
        flash('Schedule added successfully', 'success')
        return redirect(url_for('maintenance.schedule'))

    vehicles = conn.execute('SELECT vehicle_id, registration_no, make, model FROM vehicles').fetchall()
    schedules = conn.execute('''
        SELECT ms.*, v.registration_no, v.make, v.model,
               CASE WHEN ms.scheduled_date < date('now') AND ms.status = 'Pending' THEN 'Overdue'
                    ELSE ms.status END as status
        FROM maintenance_schedule ms
        JOIN vehicles v ON ms.vehicle_id = v.vehicle_id
        ORDER BY ms.scheduled_date ASC, ms.scheduled_km ASC
    ''').fetchall()
    conn.close()

    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('maintenance/schedule.html', vehicles=vehicles, schedules=schedules, today=today)


@maintenance_bp.route('/schedule/complete/<int:schedule_id>')
@login_required
def complete_schedule(schedule_id):
    conn = get_db_connection()
    conn.execute('UPDATE maintenance_schedule SET status = "Completed", completed_date = date("now") WHERE schedule_id = ?', (schedule_id,))
    conn.commit()
    conn.close()
    flash('Schedule marked as completed', 'success')
    return redirect(url_for('maintenance.schedule'))


@maintenance_bp.route('/schedule/cancel/<int:schedule_id>')
@login_required
def cancel_schedule(schedule_id):
    conn = get_db_connection()
    conn.execute('UPDATE maintenance_schedule SET status = "Cancelled" WHERE schedule_id = ?', (schedule_id,))
    conn.commit()
    conn.close()
    flash('Schedule cancelled', 'warning')
    return redirect(url_for('maintenance.schedule'))


@maintenance_bp.route('/schedule/delete/<int:schedule_id>')
@login_required
def delete_schedule(schedule_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM maintenance_schedule WHERE schedule_id = ?', (schedule_id,))
    conn.commit()
    conn.close()
    flash('Schedule deleted', 'danger')
    return redirect(url_for('maintenance.schedule'))