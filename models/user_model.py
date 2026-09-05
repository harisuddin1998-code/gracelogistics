from database.db_manager import get_db_connection
from datetime import datetime, timedelta
import hashlib
import secrets
import uuid

class UserModel:
    
    @staticmethod
    def verify_password(stored_hash, provided_password):
        """Verify password against stored hash"""
        try:
            # Parse the stored hash
            parts = stored_hash.split('$')
            if len(parts) != 3:
                return False
            
            algorithm = parts[0]
            salt = parts[1]
            stored_password_hash = parts[2]
            
            # Hash the provided password with the same salt
            if algorithm == 'pbkdf2:sha256:100000':
                computed_hash = hashlib.pbkdf2_hmac(
                    'sha256', 
                    provided_password.encode(), 
                    salt.encode(), 
                    100000
                ).hex()
                return computed_hash == stored_password_hash
            return False
        except Exception as e:
            print(f"Password verification error: {e}")
            return False
    
    @staticmethod
    def authenticate(username, password):
        """Authenticate user"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE username = ? AND is_active = 1', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            # Verify password
            if UserModel.verify_password(user['password_hash'], password):
                # Update last login
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('UPDATE users SET last_login = ? WHERE user_id = ?', 
                             (datetime.now().isoformat(), user['user_id']))
                conn.commit()
                conn.close()
                return dict(user)
        return None
    
    @staticmethod
    def create_user(username, email, password, full_name, role='staff'):
        """Create a new user"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Hash password
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        stored_hash = f"pbkdf2:sha256:100000${salt}${password_hash.hex()}"
        
        try:
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, full_name, role, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
            ''', (username, email, stored_hash, full_name, role))
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return user_id
        except Exception as e:
            conn.close()
            raise e
    
    @staticmethod
    def get_user_by_id(user_id):
        """Get user by ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, username, email, full_name, role, is_active, last_login, created_at FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None
    
    @staticmethod
    def get_all_users():
        """Get all users"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, username, email, full_name, role, is_active, last_login, created_at FROM users ORDER BY created_at DESC')
        users = cursor.fetchall()
        conn.close()
        return users
    
    @staticmethod
    def update_user(user_id, data):
        """Update user"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users SET full_name = ?, role = ?, is_active = ?
            WHERE user_id = ?
        ''', (data['full_name'], data['role'], data['is_active'], user_id))
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def change_password(user_id, new_password):
        """Change user password"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', new_password.encode(), salt.encode(), 100000)
        stored_hash = f"pbkdf2:sha256:100000${salt}${password_hash.hex()}"
        
        cursor.execute('UPDATE users SET password_hash = ? WHERE user_id = ?', (stored_hash, user_id))
        conn.commit()
        conn.close()
        return True
    
    @staticmethod
    def create_session(user_id, ip_address=None, user_agent=None):
        """Create user session"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(days=7)
        
        cursor.execute('''
            INSERT INTO user_sessions (session_id, user_id, ip_address, user_agent, expires_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, user_id, ip_address, user_agent, expires_at.isoformat()))
        conn.commit()
        conn.close()
        return session_id
    
    @staticmethod
    def get_session(session_id):
        """Get session by ID"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.*, u.username, u.full_name, u.role 
            FROM user_sessions s
            JOIN users u ON s.user_id = u.user_id
            WHERE s.session_id = ? AND s.expires_at > datetime('now')
        ''', (session_id,))
        session = cursor.fetchone()
        conn.close()
        return dict(session) if session else None
    
    @staticmethod
    def delete_session(session_id):
        """Delete session (logout)"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM user_sessions WHERE session_id = ?', (session_id,))
        conn.commit()
        conn.close()
        return True