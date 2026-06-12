import os
from datetime import datetime
import json
import sqlite3
from dotenv import load_dotenv

load_dotenv()

# MySQL connection config from environment variables
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'yatra_ai'),
}

# Aiven and other cloud MySQL providers require SSL
if os.getenv('MYSQL_SSL', '').lower() == 'true':
    import ssl
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    DB_CONFIG['ssl_disabled'] = False
    DB_CONFIG['tls_versions'] = ['TLSv1.2', 'TLSv1.3']

# Determine SQLite path
if os.getenv('VERCEL'):
    SQLITE_PATH = '/tmp/yatra_data.db'
else:
    SQLITE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'yatra_data.db')

# Check if MySQL connector is installed
try:
    import mysql.connector
    from mysql.connector import pooling
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

DB_TYPE = 'mysql'

# Auto-detect whether to use MySQL or fall back to SQLite
if not MYSQL_AVAILABLE:
    print("[WARN] mysql-connector-python not installed. Falling back to SQLite.")
    DB_TYPE = 'sqlite'
else:
    try:
        # Quick test connection with a short timeout to check if host is reachable/online
        test_conn = mysql.connector.connect(
            connection_timeout=2,
            **DB_CONFIG
        )
        test_conn.close()
        print("[OK] MySQL server is online. Using MySQL database.")
    except Exception as e:
        print(f"[WARN] MySQL database unreachable or offline ({e}). Falling back to SQLite.")
        DB_TYPE = 'sqlite'

# Connection pool for MySQL
connection_pool = None

def get_connection():
    """Get a connection based on the DB_TYPE (mysql or sqlite)."""
    global DB_TYPE, connection_pool
    if DB_TYPE == 'sqlite':
        conn = sqlite3.connect(SQLITE_PATH)
        return conn
    else:
        try:
            if connection_pool is None:
                connection_pool = pooling.MySQLConnectionPool(
                    pool_name="yatra_pool",
                    pool_size=2,
                    pool_reset_session=True,
                    **DB_CONFIG
                )
            conn = connection_pool.get_connection()
            conn.ping(reconnect=True, attempts=3, delay=1)
            return conn
        except Exception:
            # Fallback to direct connection if pool fails
            conn = mysql.connector.connect(**DB_CONFIG)
            conn.ping(reconnect=True, attempts=3, delay=1)
            return conn

def format_query(query):
    """Dynamically adapts placeholders for the active database engine."""
    if DB_TYPE == 'sqlite':
        return query.replace('%s', '?')
    return query

def close_connection(conn):
    """Safely closes connection for either SQLite or MySQL."""
    if conn:
        try:
            if hasattr(conn, 'is_connected'):
                if conn.is_connected():
                    conn.close()
            else:
                conn.close()
        except Exception as e:
            print(f"Error closing connection: {e}")

def init_db():
    """Initialize the database and create tables if they don't exist."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        if DB_TYPE == 'sqlite':
            # Create SQLite tables and indices
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ai_type TEXT,
                    user_message TEXT,
                    bot_response TEXT,
                    user_id INTEGER DEFAULT NULL
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON chat_history (user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON chat_history (timestamp)')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    google_id TEXT UNIQUE,
                    name TEXT,
                    email TEXT UNIQUE,
                    picture_url TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        else:
            # Create MySQL tables and indices
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ai_type VARCHAR(50),
                    user_message TEXT,
                    bot_response LONGTEXT,
                    user_id INT DEFAULT NULL,
                    INDEX idx_user_id (user_id),
                    INDEX idx_timestamp (timestamp)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    google_id VARCHAR(255) UNIQUE,
                    name VARCHAR(255),
                    email VARCHAR(255) UNIQUE,
                    picture_url TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
        
        conn.commit()
        cursor.close()
        print(f"[OK] Database initialized successfully using {DB_TYPE.upper()}.")
    except Exception as e:
        print(f"[ERROR] Database initialization error: {e}")
    finally:
        close_connection(conn)


def log_interaction(ai_type, user_message, bot_response, user_id=None):
    """Logs a chat interaction into the database."""
    if isinstance(bot_response, dict):
        bot_response_str = json.dumps(bot_response)
    else:
        bot_response_str = str(bot_response)
        
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(format_query('''
            INSERT INTO chat_history (timestamp, ai_type, user_message, bot_response, user_id)
            VALUES (%s, %s, %s, %s, %s)
        '''), (datetime.now(), ai_type, user_message, bot_response_str, user_id))
        conn.commit()
        cursor.close()
    except Exception as e:
        print(f"Database Error in log_interaction: {e}")
    finally:
        close_connection(conn)


def save_google_user(google_id, name, email, picture_url):
    """Saves or updates a Google authenticated user. Returns the user id."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check if user already exists
        cursor.execute(format_query("SELECT id FROM users WHERE google_id = %s"), (google_id,))
        row = cursor.fetchone()
        
        if row:
            cursor.execute(format_query('''
                UPDATE users 
                SET name = %s, email = %s, picture_url = %s 
                WHERE google_id = %s
            '''), (name, email, picture_url, google_id))
            user_id = row[0]
        else:
            cursor.execute(format_query('''
                INSERT INTO users (google_id, name, email, picture_url, created_at)
                VALUES (%s, %s, %s, %s, %s)
            '''), (google_id, name, email, picture_url, datetime.now()))
            user_id = cursor.lastrowid
            
        conn.commit()
        cursor.close()
        return user_id
    except Exception as e:
        print(f"Database Error in save_google_user: {e}")
        raise e
    finally:
        close_connection(conn)


def get_user_id_by_google_id(google_id):
    """Retrieve internal user ID by Google ID for authentication."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(format_query("SELECT id FROM users WHERE google_id = %s"), (google_id,))
        row = cursor.fetchone()
        cursor.close()
        return row[0] if row else None
    except Exception as e:
        print(f"Database Error in get_user_id_by_google_id: {e}")
        return None
    finally:
        close_connection(conn)


def get_logs(user_id):
    """Fetch all chat logs for a given user, ordered by newest first."""
    conn = None
    try:
        conn = get_connection()
        if DB_TYPE == 'sqlite':
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                format_query("SELECT * FROM chat_history WHERE user_id = %s ORDER BY timestamp DESC"),
                (user_id,)
            )
            rows = [dict(r) for r in cursor.fetchall()]
        else:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                format_query("SELECT * FROM chat_history WHERE user_id = %s ORDER BY timestamp DESC"),
                (user_id,)
            )
            rows = cursor.fetchall()
        cursor.close()
        
        # Convert datetime objects to ISO strings for JSON serialization
        for row in rows:
            ts = row.get('timestamp')
            if isinstance(ts, datetime):
                row['timestamp'] = ts.isoformat()
            elif isinstance(ts, str) and ' ' in ts:
                row['timestamp'] = ts.replace(' ', 'T')
        
        return rows
    except Exception as e:
        print(f"Database Error in get_logs: {e}")
        return []
    finally:
        close_connection(conn)


def get_log(log_id):
    """Fetch a single chat log by its ID."""
    conn = None
    try:
        conn = get_connection()
        if DB_TYPE == 'sqlite':
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(format_query("SELECT * FROM chat_history WHERE id = %s"), (log_id,))
            row = cursor.fetchone()
            if row:
                row = dict(row)
        else:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(format_query("SELECT * FROM chat_history WHERE id = %s"), (log_id,))
            row = cursor.fetchone()
        cursor.close()
        
        if row:
            ts = row.get('timestamp')
            if isinstance(ts, datetime):
                row['timestamp'] = ts.isoformat()
            elif isinstance(ts, str) and ' ' in ts:
                row['timestamp'] = ts.replace(' ', 'T')
        
        return row
    except Exception as e:
        print(f"Database Error in get_log: {e}")
        return None
    finally:
        close_connection(conn)


def delete_log(log_id):
    """Delete a chat log by its ID. Returns True if deleted, False otherwise."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(format_query("DELETE FROM chat_history WHERE id = %s"), (log_id,))
        rows_affected = cursor.rowcount
        conn.commit()
        cursor.close()
        return rows_affected > 0
    except Exception as e:
        print(f"Database Error in delete_log: {e}")
        raise e
    finally:
        close_connection(conn)


# Initialize the database when this module is imported
init_db()
