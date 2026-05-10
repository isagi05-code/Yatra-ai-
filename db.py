import os
import mysql.connector
from mysql.connector import pooling
from datetime import datetime
import json
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

# Connection pool for better performance
connection_pool = None

def get_connection():
    """Get a connection from the pool, or create a direct connection as fallback."""
    global connection_pool
    try:
        if connection_pool is None:
            connection_pool = pooling.MySQLConnectionPool(
                pool_name="yatra_pool",
                pool_size=5,
                pool_reset_session=True,
                **DB_CONFIG
            )
        return connection_pool.get_connection()
    except Exception:
        # Fallback to direct connection if pool fails
        return mysql.connector.connect(**DB_CONFIG)


def init_db():
    """Initialize the MySQL database and create tables if they don't exist."""
    try:
        # First connect WITHOUT specifying a database to create it
        init_config = DB_CONFIG.copy()
        db_name = init_config.pop('database')
        
        conn = mysql.connector.connect(**init_config)
        cursor = conn.cursor()
        
        # Create database if it doesn't exist
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.execute(f"USE `{db_name}`")
        
        # Create chat_history table
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
        
        # Create users table
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
        conn.close()
        print("[OK] MySQL database initialized successfully.")
    except mysql.connector.Error as e:
        print(f"[ERROR] MySQL initialization error: {e}")
        print("   Make sure MySQL is running and credentials in .env are correct.")


def log_interaction(ai_type, user_message, bot_response, user_id=None):
    """Logs a chat interaction into the MySQL database."""
    if isinstance(bot_response, dict):
        bot_response_str = json.dumps(bot_response)
    else:
        bot_response_str = str(bot_response)
        
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO chat_history (timestamp, ai_type, user_message, bot_response, user_id)
            VALUES (%s, %s, %s, %s, %s)
        ''', (datetime.now(), ai_type, user_message, bot_response_str, user_id))
        conn.commit()
        cursor.close()
    except Exception as e:
        print(f"Database Error: {e}")
    finally:
        if conn and conn.is_connected():
            conn.close()


def save_google_user(google_id, name, email, picture_url):
    """Saves or updates a Google authenticated user. Returns the user id."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check if user already exists
        cursor.execute("SELECT id FROM users WHERE google_id = %s", (google_id,))
        row = cursor.fetchone()
        
        if row:
            cursor.execute('''
                UPDATE users 
                SET name = %s, email = %s, picture_url = %s 
                WHERE google_id = %s
            ''', (name, email, picture_url, google_id))
            user_id = row[0]
        else:
            cursor.execute('''
                INSERT INTO users (google_id, name, email, picture_url, created_at)
                VALUES (%s, %s, %s, %s, %s)
            ''', (google_id, name, email, picture_url, datetime.now()))
            user_id = cursor.lastrowid
            
        conn.commit()
        cursor.close()
        return user_id
    except Exception as e:
        print(f"Database Error in save_google_user: {e}")
        return None
    finally:
        if conn and conn.is_connected():
            conn.close()


def get_logs(user_id):
    """Fetch all chat logs for a given user, ordered by newest first."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM chat_history WHERE user_id = %s ORDER BY timestamp DESC",
            (user_id,)
        )
        rows = cursor.fetchall()
        cursor.close()
        
        # Convert datetime objects to ISO strings for JSON serialization
        for row in rows:
            if isinstance(row.get('timestamp'), datetime):
                row['timestamp'] = row['timestamp'].isoformat()
        
        return rows
    except Exception as e:
        print(f"Database Error in get_logs: {e}")
        return []
    finally:
        if conn and conn.is_connected():
            conn.close()


def get_log(log_id):
    """Fetch a single chat log by its ID."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM chat_history WHERE id = %s", (log_id,))
        row = cursor.fetchone()
        cursor.close()
        
        if row and isinstance(row.get('timestamp'), datetime):
            row['timestamp'] = row['timestamp'].isoformat()
        
        return row
    except Exception as e:
        print(f"Database Error in get_log: {e}")
        return None
    finally:
        if conn and conn.is_connected():
            conn.close()


def delete_log(log_id):
    """Delete a chat log by its ID. Returns True if deleted, False otherwise."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_history WHERE id = %s", (log_id,))
        rows_affected = cursor.rowcount
        conn.commit()
        cursor.close()
        return rows_affected > 0
    except Exception as e:
        print(f"Database Error in delete_log: {e}")
        return False
    finally:
        if conn and conn.is_connected():
            conn.close()


# Initialize the database when this module is imported
init_db()
