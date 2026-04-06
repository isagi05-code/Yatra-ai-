import sqlite3
import os
from datetime import datetime
import json

DB_PATH = os.path.join(os.path.dirname(__file__), 'yatra_data.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Create table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            ai_type TEXT,
            user_message TEXT,
            bot_response TEXT,
            user_id INTEGER DEFAULT NULL
        )
    ''')
    
    # Safely try to add user_id column if the table was created previously without it
    try:
        cursor.execute('ALTER TABLE chat_history ADD COLUMN user_id INTEGER DEFAULT NULL')
    except sqlite3.OperationalError:
        pass # Column already exists
    
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            google_id TEXT UNIQUE,
            name TEXT,
            email TEXT UNIQUE,
            picture_url TEXT,
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

def log_interaction(ai_type, user_message, bot_response, user_id=None):
    """
    Logs an interaction from the AI into the SQLite database.
    """
    # Ensure bot_response is a string (app.py returns dict, companion returns string)
    if isinstance(bot_response, dict):
        bot_response_str = json.dumps(bot_response)
    else:
        bot_response_str = str(bot_response)
        
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO chat_history (timestamp, ai_type, user_message, bot_response, user_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (datetime.now().isoformat(), ai_type, user_message, bot_response_str, user_id))
        conn.commit()
    except Exception as e:
        print(f"Database Error: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

# Initialize the database immediately when imported
init_db()

def save_google_user(google_id, name, email, picture_url):
    """
    Saves or updates a Google authenticated user in the database.
    Returns the auto-generated user id.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if user already exists
        cursor.execute("SELECT id FROM users WHERE google_id = ?", (google_id,))
        row = cursor.fetchone()
        
        if row:
            # Update user info if changed
            cursor.execute('''
                UPDATE users 
                SET name = ?, email = ?, picture_url = ? 
                WHERE google_id = ?
            ''', (name, email, picture_url, google_id))
            user_id = row[0]
        else:
            # Insert new user
            cursor.execute('''
                INSERT INTO users (google_id, name, email, picture_url, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (google_id, name, email, picture_url, datetime.now().isoformat()))
            user_id = cursor.lastrowid
            
        conn.commit()
        return user_id
    except Exception as e:
        print(f"Database Error in save_google_user: {e}")
        return None
    finally:
        if 'conn' in locals() and conn:
            conn.close()
