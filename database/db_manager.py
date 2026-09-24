import sqlite3
import os
import re

DB_PATH = 'instance/vehicle_management.db'

def get_db_connection():
    """Create and return database connection"""
    os.makedirs('instance', exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize database with schema"""
    os.makedirs('instance', exist_ok=True)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Read and execute schema.sql
    schema_path = 'database/schema.sql'
    if os.path.exists(schema_path):
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
            # Split by semicolon and execute each statement
            statements = schema_sql.split(';')
            for statement in statements:
                if statement.strip():
                    try:
                        cursor.execute(statement)
                    except Exception as e:
                        print(f"Warning: {e}")
        conn.commit()
        print("Database schema created successfully!")
    else:
        print(f"Schema file not found at {schema_path}")
    
    # Verify users table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if not cursor.fetchone():
        print("ERROR: Users table was not created!")
    
    conn.close()
    print("Database initialized successfully!")

# Tables whose NOT NULL constraints must stay (login / sessions are not data-entry forms)
_KEEP_STRICT_TABLES = ('users', 'user_sessions')


def _strip_not_null(create_sql):
    """Remove NOT NULL from a CREATE TABLE statement (keeps 'IS NOT NULL' inside CHECKs)."""
    return re.sub(
        r'(\bIS\s+)?\bNOT\s+NULL\b(\s+ON\s+CONFLICT\s+\w+)?',
        lambda m: m.group(0) if m.group(1) else '',
        create_sql,
        flags=re.IGNORECASE,
    )


def _rebuild_table_without_not_null(conn, name, create_sql):
    """SQLite cannot drop NOT NULL in place, so rebuild the table (official 12-step recipe)."""
    tmp = f'{name}__relax_tmp'
    header = re.match(
        r'\s*CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:"[^"]+"|`[^`]+`|\[[^\]]+\]|\w+)',
        create_sql, flags=re.IGNORECASE)
    if not header:
        raise ValueError(f'cannot parse CREATE TABLE for {name}')
    new_sql = f'CREATE TABLE "{tmp}"' + _strip_not_null(create_sql[header.end():])

    columns = [row[1] for row in conn.execute(f'PRAGMA table_info("{name}")')]
    column_list = ', '.join(f'"{c}"' for c in columns)
    extras = conn.execute(
        "SELECT sql FROM sqlite_master WHERE tbl_name = ? AND type IN ('index', 'trigger') AND sql IS NOT NULL",
        (name,)).fetchall()

    try:  # AUTOINCREMENT counter, so ids of deleted rows are not handed out again
        old_seq = conn.execute('SELECT seq FROM sqlite_sequence WHERE name = ?', (name,)).fetchone()
    except sqlite3.OperationalError:  # no AUTOINCREMENT table exists at all
        old_seq = None

    conn.execute('BEGIN')
    try:
        conn.execute(new_sql)
        conn.execute(f'INSERT INTO "{tmp}" ({column_list}) SELECT {column_list} FROM "{name}"')
        old_count = conn.execute(f'SELECT COUNT(*) FROM "{name}"').fetchone()[0]
        new_count = conn.execute(f'SELECT COUNT(*) FROM "{tmp}"').fetchone()[0]
        if old_count != new_count:
            raise RuntimeError(f'row count mismatch for {name}: {old_count} != {new_count}')
        conn.execute(f'DROP TABLE "{name}"')
        conn.execute(f'ALTER TABLE "{tmp}" RENAME TO "{name}"')
        for (extra_sql,) in extras:
            conn.execute(extra_sql)
        if old_seq and old_seq[0] is not None:
            conn.execute('UPDATE sqlite_sequence SET seq = MAX(seq, ?) WHERE name = ?', (old_seq[0], name))
        conn.execute('COMMIT')
    except Exception:
        conn.execute('ROLLBACK')
        raise


def relax_not_null_constraints():
    """Let every data-entry table accept empty (NULL) values.

    Older databases were created with NOT NULL on columns such as vehicles.make or
    fuel_consumption.liters, so saving a form with a blank field failed inside SQLite.
    This rebuilds only the affected tables (a backup of the database is taken first) and
    is a no-op once nothing is left to relax.  UNIQUE and CHECK constraints are kept.
    Returns the list of tables that were rebuilt.
    """
    if not os.path.exists(DB_PATH):
        return []

    conn = sqlite3.connect(DB_PATH)
    conn.isolation_level = None  # manual BEGIN/COMMIT
    rebuilt = []
    try:
        tables = conn.execute(
            "SELECT name, sql FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' AND sql IS NOT NULL"
        ).fetchall()

        pending = []
        for name, create_sql in tables:
            if name in _KEEP_STRICT_TABLES or name.endswith('__relax_tmp'):
                continue
            if any(col[3] and not col[5] for col in conn.execute(f'PRAGMA table_info("{name}")')):
                pending.append((name, create_sql))
        if not pending:
            return []

        os.makedirs('backups', exist_ok=True)
        from datetime import datetime
        import shutil
        backup_file = f'backups/pre_relax_constraints_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        shutil.copy2(DB_PATH, backup_file)
        print(f'Backup created before relaxing constraints: {backup_file}')

        conn.execute('PRAGMA foreign_keys = OFF')
        for name, create_sql in pending:
            try:
                _rebuild_table_without_not_null(conn, name, create_sql)
                rebuilt.append(name)
            except Exception as exc:
                print(f'Warning: could not relax NOT NULL on {name}: {exc}')
        if rebuilt:
            print('NOT NULL constraints relaxed on: ' + ', '.join(rebuilt))
    finally:
        conn.close()
    return rebuilt


def backup_database():
    """Backup database"""
    import shutil
    from datetime import datetime
    
    os.makedirs('backups', exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'backups/vehicle_management_backup_{timestamp}.db'
    
    if os.path.exists(DB_PATH):
        shutil.copy2(DB_PATH, backup_file)
        return backup_file
    return None