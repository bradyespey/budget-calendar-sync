# app.py

import asyncio
import os
from flask import Flask, jsonify, request, Response
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from scripts.check_review_count import get_review_count
from scripts.get_chase_balance import get_chase_balance_async as get_chase_balance
from scripts.refresh_accounts import refresh_accounts

app = Flask(__name__)

# Retrieve API_AUTH from environment variables
API_AUTH = os.getenv("API_AUTH")
if not API_AUTH:
    raise ValueError("API_AUTH must be set in the environment.")

# Split API_AUTH into username and password
if ':' not in API_AUTH:
    raise ValueError("API_AUTH must be in the format 'username:password'.")
BASIC_AUTH_USER, BASIC_AUTH_PASS = API_AUTH.split(":", 1)

def check_auth(username, password):
    """Check if a username/password combination is valid."""
    print(f"Received Credentials - Username: {username}, Password: {password}")  # Debug print
    return username == BASIC_AUTH_USER and password == BASIC_AUTH_PASS

def requires_auth(func):
    """Decorator to enforce Basic Auth on routes."""
    def wrapper(*args, **kwargs):
        auth = request.authorization
        print(f"🔍 Flask received auth: {auth}")  # Debug print
        
        if not auth:
            print("❌ No auth header received.")
            return Response("Unauthorized", 401, {"WWW-Authenticate": "Basic realm='Login Required'"})
        
        print(f"🛠️ Checking credentials: Username={auth.username}, Password={auth.password}")
        
        if not check_auth(auth.username, auth.password):
            print(f"❌ Invalid credentials received: {auth.username}:{auth.password}")
            return Response("Unauthorized", 401, {"WWW-Authenticate": "Basic realm='Login Required'"})
        
        print("✅ Authentication successful!")
        return func(*args, **kwargs)
    
    wrapper.__name__ = func.__name__  # Flask compatibility fix
    return wrapper

@app.route("/transactions_review", methods=["GET"])
@requires_auth
def transactions_review_endpoint():
    try:
        count = get_review_count()  # Uses Selenium
        return jsonify({"transactions_to_review": count}), 200
    except Exception as e:
        return jsonify({"error": f"Error occurred while fetching review count: {str(e)}"}), 500

@app.route("/chase_balance", methods=["GET"])
@requires_auth
def chase_balance_endpoint():
    try:
        balance = asyncio.run(get_chase_balance())  # Uses aiohttp
        return jsonify({"chase_balance": balance}), 200
    except Exception as e:
        return jsonify({"error": f"Error occurred while fetching Chase balance: {str(e)}"}), 500

@app.route("/refresh_accounts", methods=["GET", "POST"])
@requires_auth
def refresh_accounts_endpoint():
    try:
        refresh_accounts()  # Uses Selenium
        return jsonify({"status": "Accounts refreshed successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Error occurred while refreshing accounts: {str(e)}"}), 500
    
@app.route("/food_log_count", methods=["GET", "POST"])
@requires_auth
def food_log_count_endpoint():
    global stored_photo_count
    if request.method == "POST":
        try:
            data = request.get_json()
            if not data or "photo_count" not in data:
                return jsonify({"error": "Missing photo_count"}), 400
            stored_photo_count = int(data["photo_count"])
            return jsonify({"photo_count": stored_photo_count}), 200
        except Exception as e:
            return jsonify({"error": f"Error processing food log count: {str(e)}"}), 500
    else:  # GET
        return jsonify({"photo_count": stored_photo_count if 'stored_photo_count' in globals() else 0}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)