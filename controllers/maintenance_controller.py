from flask import Blueprint, render_template, request, redirect, url_for, flash, session, make_response
from functools import wraps
from datetime import datetime
from database.db_manager import get_db_connection
import io
import pandas as pd
from utils.helpers import (form_text, form_text_or_none, form_float, form_float_or_none,
                           form_int, form_int_or_none, form_date, form_id)

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
        # Nothing here is mandatory: blank fields are stored as empty values.
        maintenance_type = form_text(request.form, 'maintenance_type')
        vehicle_id = form_id(request.form, 'vehicle_id')
        date = form_date(request.form, 'date')
        cost = form_float(request.form, 'cost')
        notes = form_text(request.form, 'notes')
        created_by = session.get('user_id')

        conn = get_db_connection()
        try:
            # ----- TUNING -----
            if maintenance_type == 'tuning':
                conn.execute('''INSERT INTO tuning 
                    (vehicle_id, date, tuning_type, cost, technician_name, 
                     before_performance, after_performance, notes, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (vehicle_id, date, form_text_or_none(request.form, 'tuning_type'), cost,
                     form_text(request.form, 'technician_name'),
                     form_text(request.form, 'before_performance'),
                     form_text(request.form, 'after_performance'), notes, created_by))

            # ----- ELECTRICAL WORK -----
            elif maintenance_type == 'electrical':
                conn.execute('''INSERT INTO electrical_work 
                    (vehicle_id, date, work_type, cost, technician_name, parts_used, hours_spent, notes, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (vehicle_id, date, form_text_or_none(request.form, 'work_type'), cost,
                     form_text(request.form, 'technician_name'),
                     form_text(request.form, 'parts_used'),
                     form_float_or_none(request.form, 'hours_spent'), notes, created_by))

            # ----- BODY WORK -----
            elif maintenance_type == 'body_work':
                conn.execute('''INSERT INTO body_work 
                    (vehicle_id, date, work_type, cost, workshop_name, painter_name, 
                     color_code, panels_repaired, warranty_months, notes, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (vehicle_id, date, form_text_or_none(request.form, 'work_type'), cost,
                     form_text(request.form, 'workshop_name'),
                     form_text(request.form, 'painter_name'),
                     form_text(request.form, 'color_code'),
                     form_text(request.form, 'panels_repaired'),
                     form_int_or_none(request.form, 'warranty_months'), notes, created_by))

            # ----- TIRE CHANGE -----
            elif maintenance_type == 'tire_change':
                quantity = form_int(request.form, 'quantity', 1)
                cost_per_tire = form_float(request.form, 'cost_per_tire')
                total_cost = cost  # already the total cost from form
                alignment_done = 1 if request.form.get('alignment_done') else 0
                balancing_done = 1 if request.form.get('balancing_done') else 0

                conn.execute('''INSERT INTO tire_change 
                    (vehicle_id, date, tire_position, tire_brand, tire_size, quantity, 
                     cost_per_tire, total_cost, alignment_done, balancing_done, 
                     old_tire_condition, next_rotation_km, workshop_name, notes, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (vehicle_id, date, form_text_or_none(request.form, 'tire_position'),
                     form_text(request.form, 'tire_brand'), form_text(request.form, 'tire_size'),
                     quantity, cost_per_tire, total_cost, alignment_done, balancing_done,
                     form_text(request.form, 'old_tire_condition'),
                     form_int_or_none(request.form, 'next_rotation_km'),
                     form_text(request.form, 'workshop_name'), notes, created_by))

            # ----- ROUTINE MAINTENANCE (maintenance table) -----
            # oil change, filter change, or - when no type was chosen - a general record
            else:
                if maintenance_type == 'oil_change':
                    maint_type = 'Oil Change'
                    quantity = form_float(request.form, 'quantity', 0)
                elif maintenance_type == 'filter_change':
                    maint_type = form_text(request.form, 'filter_type')  # e.g., 'Air Filter', 'Oil Filter'
                    quantity = form_int(request.form, 'quantity', 1)
                else:
                    maint_type = ''
                    quantity = form_int(request.form, 'quantity', 1)

                unit_price = cost / quantity if quantity else cost

                conn.execute('''INSERT INTO maintenance 
                    (vehicle_id, maintenance_type, date, cost, quantity, unit_price, 
                     next_due_km, next_due_date, mechanic_name, notes, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (vehicle_id, maint_type, date, cost, quantity, unit_price,
                     form_int_or_none(request.form, 'next_due_km'),
                     form_date(request.form, 'next_due_date'),
                     form_text(request.form, 'mechanic_name'), notes, created_by))

            conn.commit()
            label = maintenance_type.replace("_", " ").title() or 'Maintenance'
            flash(f'{label} record saved successfully!', 'success')

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

    # 1. Routine maintenance
    maint_records = conn.execute('''
        SELECT m.maintenance_id as id, m.vehicle_id, m.date, m.cost, m.next_due_km, m.next_due_date,
               m.mechanic_name, m.notes, m.maintenance_type as type, v.registration_no, v.make, v.model,
               'maintenance' as category
        FROM maintenance m
        LEFT JOIN vehicles v ON m.vehicle_id = v.vehicle_id
        WHERE (? = '' OR m.vehicle_id = ?)
        ORDER BY m.date DESC
    ''', (selected_vehicle, selected_vehicle)).fetchall()

    # 2. Tuning
    tuning_records = conn.execute('''
        SELECT t.tuning_id as id, t.vehicle_id, t.date, t.cost, NULL as next_due_km, NULL as next_due_date,
               t.technician_name as mechanic_name, t.notes, t.tuning_type as type, v.registration_no, v.make, v.model,
               'tuning' as category, t.tuning_type as service_type, t.technician_name, t.notes as description
        FROM tuning t
        LEFT JOIN vehicles v ON t.vehicle_id = v.vehicle_id
        WHERE (? = '' OR t.vehicle_id = ?)
        ORDER BY t.date DESC
    ''', (selected_vehicle, selected_vehicle)).fetchall()

    # 3. Electrical
    elec_records = conn.execute('''
        SELECT e.electrical_id as id, e.vehicle_id, e.date, e.cost, NULL as next_due_km, NULL as next_due_date,
               e.technician_name as mechanic_name, e.notes, e.work_type as type, v.registration_no, v.make, v.model,
               'electrical' as category, e.work_type as service_type, e.technician_name, e.parts_used as description
        FROM electrical_work e
        LEFT JOIN vehicles v ON e.vehicle_id = v.vehicle_id
        WHERE (? = '' OR e.vehicle_id = ?)
        ORDER BY e.date DESC
    ''', (selected_vehicle, selected_vehicle)).fetchall()

    # 4. Body work
    body_records = conn.execute('''
        SELECT b.body_work_id as id, b.vehicle_id, b.date, b.cost, NULL as next_due_km, NULL as next_due_date,
               COALESCE(b.workshop_name, b.painter_name) as mechanic_name, b.notes, b.work_type as type, v.registration_no, v.make, v.model,
               'body_work' as category
        FROM body_work b
        LEFT JOIN vehicles v ON b.vehicle_id = v.vehicle_id
        WHERE (? = '' OR b.vehicle_id = ?)
        ORDER BY b.date DESC
    ''', (selected_vehicle, selected_vehicle)).fetchall()

    # 5. Tire change
    tire_records = conn.execute('''
        SELECT tr.tire_id as id, tr.vehicle_id, tr.date, tr.total_cost as cost, tr.next_rotation_km as next_due_km, NULL as next_due_date,
               tr.workshop_name as mechanic_name, tr.notes, ('Tire Change' || CASE WHEN tr.tire_position IS NULL OR tr.tire_position = '' THEN '' ELSE ' (' || tr.tire_position || ')' END) as type, v.registration_no, v.make, v.model,
               'tire_change' as category
        FROM tire_change tr
        LEFT JOIN vehicles v ON tr.vehicle_id = v.vehicle_id
        WHERE (? = '' OR tr.vehicle_id = ?)
        ORDER BY tr.date DESC
    ''', (selected_vehicle, selected_vehicle)).fetchall()

    conn.close()

    # Combine all records
    all_records = []
    tuning_and_elec = []
    for r in maint_records: all_records.append(dict(r))
    for r in tuning_records:
        d = dict(r)
        all_records.append(d)
        tuning_and_elec.append(d)
    for r in elec_records:
        d = dict(r)
        all_records.append(d)
        tuning_and_elec.append(d)
    for r in body_records: all_records.append(dict(r))
    for r in tire_records: all_records.append(dict(r))

    # records saved without a date sort last
    all_records.sort(key=lambda x: x['date'] or '', reverse=True)
    tuning_and_elec.sort(key=lambda x: x['date'] or '', reverse=True)

    return render_template('maintenance/history.html', 
                           vehicles=vehicles, 
                           records=all_records,
                           tuning_records=tuning_and_elec,
                           selected_vehicle=selected_vehicle)


@maintenance_bp.route('/delete/<category>/<int:record_id>')
@login_required
def delete_maintenance_record(category, record_id):
    table_map = {
        'maintenance': ('maintenance', 'maintenance_id'),
        'tuning': ('tuning', 'tuning_id'),
        'electrical': ('electrical_work', 'electrical_id'),
        'body_work': ('body_work', 'body_work_id'),
        'tire_change': ('tire_change', 'tire_id'),
    }
    if category in table_map:
        tbl, id_col = table_map[category]
        try:
            conn = get_db_connection()
            conn.execute(f"DELETE FROM {tbl} WHERE {id_col} = ?", (record_id,))
            conn.commit()
            conn.close()
            flash('Maintenance record deleted successfully!', 'success')
        except Exception as e:
            flash(f'Error deleting maintenance record: {str(e)}', 'danger')
    else:
        flash('Invalid record category!', 'danger')
    return redirect(url_for('maintenance.history'))



# ============================================================
# REPORT – COST SUMMARY
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

    def add_summary(name, data_list, cost_key='cost'):
        nonlocal total_cost
        if data_list:
            cnt = len(data_list)
            total = sum((row[cost_key] or 0) for row in data_list)
            avg = total / cnt if cnt else 0
            dates = [row['date'] for row in data_list if row['date']]
            first = min(dates) if dates else None
            last = max(dates) if dates else None
            summary.append({
                'maintenance_type': name,
                'total_count': cnt,
                'total_cost': total,
                'avg_cost': avg,
                'first_date': first,
                'last_date': last
            })
            total_cost += total

    # Build WHERE clause
    veh_filter = "" if not selected_vehicle else f"AND vehicle_id = {selected_vehicle}"
    date_filter = ""
    if start_date and end_date:
        date_filter = f"AND date BETWEEN '{start_date}' AND '{end_date}'"
    elif start_date:
        date_filter = f"AND date >= '{start_date}'"
    elif end_date:
        date_filter = f"AND date <= '{end_date}'"

    # Maintenance table – group by maintenance_type
    maint_types = conn.execute(f'''
        SELECT maintenance_type, COUNT(*) as cnt, SUM(cost) as total, AVG(cost) as avg, 
               MIN(date) as first, MAX(date) as last
        FROM maintenance WHERE 1=1 {veh_filter} {date_filter}
        GROUP BY maintenance_type
    ''').fetchall()
    for mt in maint_types:
        summary.append({
            'maintenance_type': mt['maintenance_type'] or 'Not specified',
            'total_count': mt['cnt'],
            'total_cost': mt['total'] or 0,
            'avg_cost': mt['avg'] or 0,
            'first_date': mt['first'],
            'last_date': mt['last']
        })
        total_cost += (mt['total'] or 0)

    # Individual tables
    tuning = conn.execute(f"SELECT * FROM tuning WHERE 1=1 {veh_filter} {date_filter}").fetchall()
    add_summary('Tuning', tuning)

    electrical = conn.execute(f"SELECT * FROM electrical_work WHERE 1=1 {veh_filter} {date_filter}").fetchall()
    add_summary('Electrical Work', electrical)

    body = conn.execute(f"SELECT * FROM body_work WHERE 1=1 {veh_filter} {date_filter}").fetchall()
    add_summary('Body Work', body)

    tires = conn.execute(f"SELECT * FROM tire_change WHERE 1=1 {veh_filter} {date_filter}").fetchall()
    add_summary('Tire Change', tires, cost_key='total_cost')

    conn.close()
    summary.sort(key=lambda x: x['total_cost'], reverse=True)

    return render_template('maintenance/report.html', vehicles=vehicles, summary=summary, total_cost=total_cost,
                         selected_vehicle=selected_vehicle, start_date=start_date, end_date=end_date)


# ============================================================
# EXPORT TO EXCEL
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

    maint = conn.execute(f'''
        SELECT m.date, v.registration_no, 'Maintenance' as type, m.maintenance_type as sub_type, 
               m.cost, m.quantity, m.mechanic_name, m.notes
        FROM maintenance m LEFT JOIN vehicles v ON m.vehicle_id = v.vehicle_id
        WHERE 1=1 {veh_filter} {date_filter}
    ''').fetchall()
    tuning = conn.execute(f'''
        SELECT t.date, v.registration_no, 'Tuning' as type, t.tuning_type as sub_type, 
               t.cost, NULL as quantity, t.technician_name as mechanic_name, t.notes
        FROM tuning t LEFT JOIN vehicles v ON t.vehicle_id = v.vehicle_id
        WHERE 1=1 {veh_filter} {date_filter}
    ''').fetchall()
    electrical = conn.execute(f'''
        SELECT e.date, v.registration_no, 'Electrical' as type, e.work_type as sub_type, 
               e.cost, NULL as quantity, e.technician_name as mechanic_name, e.notes
        FROM electrical_work e LEFT JOIN vehicles v ON e.vehicle_id = v.vehicle_id
        WHERE 1=1 {veh_filter} {date_filter}
    ''').fetchall()
    body = conn.execute(f'''
        SELECT b.date, v.registration_no, 'Body Work' as type, b.work_type as sub_type, 
               b.cost, NULL as quantity, b.painter_name as mechanic_name, b.notes
        FROM body_work b LEFT JOIN vehicles v ON b.vehicle_id = v.vehicle_id
        WHERE 1=1 {veh_filter} {date_filter}
    ''').fetchall()
    tires = conn.execute(f'''
        SELECT tr.date, v.registration_no, 'Tire Change' as type, tr.tire_position as sub_type, 
               tr.total_cost as cost, tr.quantity, tr.workshop_name as mechanic_name, tr.notes
        FROM tire_change tr LEFT JOIN vehicles v ON tr.vehicle_id = v.vehicle_id
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
# PREVENTIVE MAINTENANCE SCHEDULE
# ============================================================
@maintenance_bp.route('/schedule', methods=['GET', 'POST'])
@login_required
def schedule():
    conn = get_db_connection()
    if request.method == 'POST':
        try:
            conn.execute('''INSERT INTO maintenance_schedule 
                            (vehicle_id, maintenance_type, scheduled_date, scheduled_km, assigned_to, notes, status)
                            VALUES (?, ?, ?, ?, ?, ?, 'Pending')''',
                         (form_id(request.form, 'vehicle_id'),
                          form_text(request.form, 'maintenance_type'),
                          form_date(request.form, 'scheduled_date'),
                          form_int_or_none(request.form, 'scheduled_km'),
                          form_text(request.form, 'assigned_to'),
                          form_text(request.form, 'notes')))
            conn.commit()
            flash('Schedule added successfully', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Database error: {str(e)}', 'danger')
        finally:
            conn.close()
        return redirect(url_for('maintenance.schedule'))

    vehicles = conn.execute('SELECT vehicle_id, registration_no, make, model FROM vehicles').fetchall()
    schedules = conn.execute('''
        SELECT ms.*, v.registration_no, v.make, v.model,
               CASE WHEN ms.scheduled_date < date('now') AND ms.status = 'Pending' THEN 'Overdue'
                    ELSE ms.status END as status
        FROM maintenance_schedule ms
        LEFT JOIN vehicles v ON ms.vehicle_id = v.vehicle_id
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