import os
import json
import traceback
import db
from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Configure the Gemini API with your key
# Make sure you have a .env file with GEMINI_API_KEY="YOUR_API_KEY"
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# System instruction to force the AI to return JSON
system_instruction = """You are an expert travel agent named Yatra.AI. 
You recommend great Airbnb properties and supply detailed itineraries.
You MUST always return your response in JSON format exactly like this:
{
   "reply": "Your conversational response here, including markdown links to properties if asked.",
   "destination": "Name of the destination",
   "itinerary": [
       { "day": 1, "activity": "Detail about day 1" },
       { "day": 2, "activity": "Detail about day 2" }
   ],
   "airbnb_links": ["Beautiful stays - https://www.airbnb.com/s/DESTINATION/homes"],
   "restaurants": ["Real Restaurant Name - Description"],
   "cafes": ["Real Cafe Name - Description"]
}
CRITICAL INSTRUCTIONS:
1. For 'airbnb_links', NEVER hallucinate specific Airbnb property URLs (like /rooms/12345) as they lead to 404 errors. Instead, provide actual working search URLs like "https://www.airbnb.com/s/[Destination]/homes".
2. For 'restaurants' and 'cafes', you MUST recommend REAL, currently existing, and highly-rated places in the destination. Do NOT make up names.
If the user hasn't chosen a destination yet, leave "destination" blank and arrays empty, but prompt them in the "reply" field."""

# System instruction for the 24/7 travel companion
companion_system_instruction = """You are Yatra.AI Travel Companion, a friendly, highly-capable 24/7 personal travel assistant. 
Your goal is to help users during their active travels. They might need help finding real-time hotels, restaurants, and cafes under their budget, need local tips, or general travel advice.
Provide practical, immediate, and localized responses like a typical AI assistant (e.g., ChatGPT, Gemini). 
Always format your responses using beautiful Markdown, utilizing headers, bold text, bullet points, and links where appropriate to make the response highly readable.
Do NOT return JSON. Provide your output entirely in Markdown text."""

@app.route('/')
def index():
    """Serve the main index.html file."""
    return app.send_static_file('index.html')

import time
from google.genai import errors

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        user_message = request.json['message']
        user_id = request.json.get('user_id')
        prompt = f"User message: {user_message}"
        
        # Add retry logic for 503 High Demand errors
        max_retries = 3
        retry_delay = 2
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json",
                    )
                )
                break # Success, exit retry loop
            except errors.ServerError as e:
                if e.code == 503 and attempt < max_retries - 1:
                    print(f"API high demand, retrying in {retry_delay} seconds (Attempt {attempt + 1}/{max_retries})...")
                    time.sleep(retry_delay)
                    retry_delay *= 2 # Exponential backoff
                else:
                    raise e # Re-raise if not 503 or max retries reached
        
        response_data = json.loads(response.text)

        db.log_interaction("Itinerary", user_message, response_data, user_id=user_id)

        return jsonify(response_data)
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        return jsonify({"reply": "Sorry, I'm having trouble connecting to the AI service."}), 500

@app.route('/api/companion', methods=['POST'])
def companion():
    try:
        user_message = request.json.get('message', '')
        context = request.json.get('context', '')
        user_id = request.json.get('user_id')
        
        if context:
            prompt = f"PREVIOUS CHAT CONTEXT:\n{context}\n\nUser's new message: {user_message}"
        else:
            prompt = f"User message: {user_message}"
        
        # Add retry logic for 503 High Demand errors
        max_retries = 3
        retry_delay = 2
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=companion_system_instruction,
                    )
                )
                break
            except errors.ServerError as e:
                if e.code == 503 and attempt < max_retries - 1:
                    print(f"API high demand, retrying in {retry_delay} seconds (Attempt {attempt + 1}/{max_retries})...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    raise e
                    
        db.log_interaction("Companion", user_message, response.text, user_id=user_id)
        
        return jsonify({"reply": response.text})
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        return jsonify({"reply": "Sorry, I'm having trouble connecting to the AI service."}), 500

@app.route('/api/logs', methods=['GET'])
def get_logs():
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify([])
            
        import sqlite3
        conn = sqlite3.connect('yatra_data.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM chat_history WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
        rows = cursor.fetchall()
        data = [dict(row) for row in rows]
        conn.close()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/logs/<int:log_id>', methods=['GET'])
def get_log(log_id):
    try:
        import sqlite3
        conn = sqlite3.connect('yatra_data.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM chat_history WHERE id = ?", (log_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return jsonify(dict(row))
        return jsonify({"error": "Not Found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/logs/<int:log_id>', methods=['DELETE'])
def delete_log(log_id):
    try:
        import sqlite3
        conn = sqlite3.connect('yatra_data.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_history WHERE id = ?", (log_id,))
        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        if rows_affected > 0:
            return jsonify({"success": True, "message": "Log deleted successfully"})
        return jsonify({"error": "Log not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

GOOGLE_CLIENT_ID = "250570628666-sk264agni60kpmnuisi8jqqbefm3l5mh.apps.googleusercontent.com"

@app.route('/api/auth/google', methods=['POST'])
def auth_google():
    try:
        # Get the credential JWT from frontend
        token = request.json.get('credential')
        if not token:
            return jsonify({'error': 'No token provided'}), 400
            
        # Verify the token with Google
        try:
            idinfo = id_token.verify_oauth2_token(
                token, 
                google_requests.Request(), 
                GOOGLE_CLIENT_ID
            )
            
            # ID token is valid. Get the user's basic info
            google_id = idinfo['sub']
            email = idinfo.get('email')
            name = idinfo.get('name')
            picture = idinfo.get('picture')
            
            # Save or update the user in SQLite database
            user_id = db.save_google_user(google_id, name, email, picture)
            
            if user_id:
                return jsonify({
                    'success': True,
                    'user': {
                        'id': user_id,
                        'name': name,
                        'email': email,
                        'picture': picture
                    }
                })
            else:
                return jsonify({'error': 'Database failed to save user'}), 500
                
        except ValueError as e:
            # Invalid token
            print(f"Invalid Google token: {e}")
            return jsonify({'error': 'Invalid token'}), 401
            
    except Exception as e:
        print(f"Auth error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    app.run(host='0.0.0.0', port=port, debug=True)