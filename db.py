import os
from datetime import datetime
import json
from dotenv import load_dotenv
from pymongo import MongoClient
from bson import ObjectId

load_dotenv()

# MongoDB connection string
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/yatra_ai')

client = None
db = None

try:
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    # Parse DB name from URI if present, otherwise default to 'yatra_ai'
    db_name = 'yatra_ai'
    if '/' in MONGODB_URI.replace('mongodb://', '').replace('mongodb+srv://', ''):
        path_part = MONGODB_URI.split('/')[-1].split('?')[0]
        if path_part:
            db_name = path_part
            
    db = client[db_name]
    # Ping to check connection
    client.admin.command('ping')
    print(f"[OK] Connected to MongoDB database '{db_name}'.")
except Exception as e:
    print(f"[ERROR] Failed to connect to MongoDB: {e}")
    db = None

def init_db():
    """Initializes MongoDB collections and indexes."""
    global db
    if db is None:
        print("[ERROR] MongoDB is not initialized. Cannot run init_db.")
        return
    try:
        # Create unique indexes for users
        db.users.create_index("google_id", unique=True)
        db.users.create_index("email", unique=True)
        
        # Create indexes for chat history queries
        db.chat_history.create_index("user_id")
        db.chat_history.create_index("timestamp")
        print("[OK] MongoDB indexes initialized successfully.")
    except Exception as e:
        print(f"[ERROR] MongoDB index initialization error: {e}")


def log_interaction(ai_type, user_message, bot_response, user_id=None):
    """Logs a chat interaction into the database."""
    if isinstance(bot_response, dict):
        bot_response_str = json.dumps(bot_response)
    else:
        bot_response_str = str(bot_response)
        
    try:
        doc = {
            "timestamp": datetime.now(),
            "ai_type": ai_type,
            "user_message": user_message,
            "bot_response": bot_response_str,
            "user_id": str(user_id) if user_id else None
        }
        db.chat_history.insert_one(doc)
    except Exception as e:
        print(f"Database Error in log_interaction: {e}")


def save_google_user(google_id, name, email, picture_url):
    """Saves or updates a Google authenticated user. Returns the user id as a string."""
    try:
        user = db.users.find_one({"google_id": google_id})
        
        if user:
            db.users.update_one(
                {"google_id": google_id},
                {"$set": {
                    "name": name,
                    "email": email,
                    "picture_url": picture_url
                }}
            )
            user_id = str(user["_id"])
        else:
            res = db.users.insert_one({
                "google_id": google_id,
                "name": name,
                "email": email,
                "picture_url": picture_url,
                "created_at": datetime.now()
            })
            user_id = str(res.inserted_id)
            
        return user_id
    except Exception as e:
        print(f"Database Error in save_google_user: {e}")
        raise e


def get_user_id_by_google_id(google_id):
    """Retrieve internal user ID by Google ID for authentication."""
    try:
        user = db.users.find_one({"google_id": google_id})
        return str(user["_id"]) if user else None
    except Exception as e:
        print(f"Database Error in get_user_id_by_google_id: {e}")
        return None


def get_logs(user_id):
    """Fetch all chat logs for a given user, ordered by newest first."""
    try:
        cursor = db.chat_history.find({"user_id": str(user_id)}).sort("timestamp", -1)
        rows = []
        for doc in cursor:
            row = {
                "id": str(doc["_id"]),
                "timestamp": doc["timestamp"].isoformat() if isinstance(doc["timestamp"], datetime) else str(doc["timestamp"]),
                "ai_type": doc.get("ai_type"),
                "user_message": doc.get("user_message"),
                "bot_response": doc.get("bot_response"),
                "user_id": doc.get("user_id")
            }
            rows.append(row)
        return rows
    except Exception as e:
        print(f"Database Error in get_logs: {e}")
        return []


def get_log(log_id):
    """Fetch a single chat log by its ID."""
    try:
        doc = db.chat_history.find_one({"_id": ObjectId(log_id)})
        if doc:
            return {
                "id": str(doc["_id"]),
                "timestamp": doc["timestamp"].isoformat() if isinstance(doc["timestamp"], datetime) else str(doc["timestamp"]),
                "ai_type": doc.get("ai_type"),
                "user_message": doc.get("user_message"),
                "bot_response": doc.get("bot_response"),
                "user_id": doc.get("user_id")
            }
        return None
    except Exception as e:
        print(f"Database Error in get_log: {e}")
        return None


def delete_log(log_id):
    """Delete a chat log by its ID. Returns True if deleted, False otherwise."""
    try:
        res = db.chat_history.delete_one({"_id": ObjectId(log_id)})
        return res.deleted_count > 0
    except Exception as e:
        print(f"Database Error in delete_log: {e}")
        raise e


# Initialize collections and indexes when imported
init_db()
