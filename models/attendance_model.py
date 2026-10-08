from database.db_manager import get_db_connection

# One row per vehicle per day.  A vehicle is either Present, or Absent for one of three reasons:
#   'In Garage'          - the car is in the workshop / not on the road
#   'Driver Absent'      - the driver did not come, so the driver is marked absent as well
#   'No Driver Assigned' - nobody is allotted to the car
# The form sends a short code for each vehicle; this maps it to what is stored.
ATTENDANCE_CODES = {
    'present':       {'status': 'Present', 'reason': None,                 'driver_status': 'Present'},
    'garage':        {'status': 'Absent',  'reason': 'In Garage',          'driver_status': 'Present'},
    'driver_absent': {'status': 'Absent',  'reason': 'Driver Absent',      'driver_status': 'Absent'},
    'no_driver':     {'status': 'Absent',  'reason': 'No Driver Assigned', 'driver_status': None},
}


def attendance_code(record):
    """Turn a stored attendance row back into its form code."""
    if record['status'] == 'Present':
        return 'present'
    return {
        'In Garage': 'garage',
        'Driver Absent': 'driver_absent',
        'No Driver Assigned': 'no_driver',
    }.get(record['reason'], 'garage')


def create_attendance_table():
    """Create the vehicle_attendance table on databases that do not have it yet."""
    conn = get_db_connection()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS vehicle_attendance (
            attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER,
            date DATE,
            status TEXT,
            reason TEXT,
            driver_id INTEGER,
            driver_status TEXT,
            notes TEXT,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (vehicle_id, date),
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(vehicle_id),
            FOREIGN KEY (driver_id) REFERENCES drivers(driver_id),
            FOREIGN KEY (created_by) REFERENCES users(user_id)
        );
        CREATE INDEX IF NOT EXISTS idx_attendance_date ON vehicle_attendance(date);
        CREATE INDEX IF NOT EXISTS idx_attendance_driver ON vehicle_attendance(driver_id);
    ''')
    conn.commit()
    conn.close()


class AttendanceModel:

    @staticmethod
    def get_day(date):
        """Saved attendance for one day, keyed by vehicle_id."""
        conn = get_db_connection()
        rows = conn.execute('SELECT * FROM vehicle_attendance WHERE date = ?', (date,)).fetchall()
        conn.close()
        return {row['vehicle_id']: row for row in rows}

    @staticmethod
    def save_day(date, entries, user_id):
        """Save (or overwrite) a day's attendance.

        entries: list of dicts with vehicle_id, driver_id, code and notes.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        for entry in entries:
            mark = ATTENDANCE_CODES[entry['code']]
            cursor.execute('''
                INSERT OR REPLACE INTO vehicle_attendance
                    (vehicle_id, date, status, reason, driver_id, driver_status, notes, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (entry['vehicle_id'], date, mark['status'], mark['reason'],
                  entry['driver_id'], mark['driver_status'] if entry['driver_id'] else None,
                  entry['notes'], user_id))
        conn.commit()
        conn.close()

    @staticmethod
    def get_vehicle_month_summary(month):
        """Per-vehicle day counts for a month (YYYY-MM)."""
        conn = get_db_connection()
        rows = conn.execute('''
            SELECT v.vehicle_id, v.registration_no, v.make, v.model,
                   COUNT(a.attendance_id) AS marked_days,
                   SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) AS present_days,
                   SUM(CASE WHEN a.reason = 'In Garage' THEN 1 ELSE 0 END) AS garage_days,
                   SUM(CASE WHEN a.reason = 'Driver Absent' THEN 1 ELSE 0 END) AS driver_absent_days,
                   SUM(CASE WHEN a.reason = 'No Driver Assigned' THEN 1 ELSE 0 END) AS no_driver_days
            FROM vehicles v
            JOIN vehicle_attendance a ON a.vehicle_id = v.vehicle_id
            WHERE strftime('%Y-%m', a.date) = ?
            GROUP BY v.vehicle_id
            ORDER BY v.registration_no
        ''', (month,)).fetchall()
        conn.close()
        return rows

    @staticmethod
    def get_driver_month_summary(month):
        """Per-driver present/absent day counts for a month (YYYY-MM)."""
        conn = get_db_connection()
        rows = conn.execute('''
            SELECT d.driver_id, d.full_name,
                   COUNT(a.attendance_id) AS marked_days,
                   SUM(CASE WHEN a.driver_status = 'Present' THEN 1 ELSE 0 END) AS present_days,
                   SUM(CASE WHEN a.driver_status = 'Absent' THEN 1 ELSE 0 END) AS absent_days,
                   GROUP_CONCAT(CASE WHEN a.driver_status = 'Absent' THEN strftime('%d', a.date) END) AS absent_dates
            FROM drivers d
            JOIN vehicle_attendance a ON a.driver_id = d.driver_id
            WHERE strftime('%Y-%m', a.date) = ?
            GROUP BY d.driver_id
            ORDER BY d.full_name
        ''', (month,)).fetchall()
        conn.close()
        return rows
