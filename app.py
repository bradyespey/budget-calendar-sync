# app.py

import asyncio
import os
from functools import wraps
from flask import Flask, jsonify, request, Response
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from scripts.check_review_count import get_review_count
from scripts.get_chase_balance import get_chase_balance_async as get_chase_balance
from scripts.refresh_accounts import refresh_accounts

app = Flask(__name__)

# Basic‑Auth config
API_AUTH = os.getenv("API_AUTH")
if not API_AUTH:
    raise RuntimeError("API_AUTH must be set in the environment as user:pass")
if ":" not in API_AUTH:
    raise RuntimeError("API_AUTH must be in the format 'username:password'")
BASIC_AUTH_USER, BASIC_AUTH_PASS = API_AUTH.split(":", 1)

def check_auth(username, password):
    return username == BASIC_AUTH_USER and password == BASIC_AUTH_PASS

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        # debug print (ASCII only)
        print(f"Flask received auth header: {auth}")
        if not auth or not check_auth(auth.username, auth.password):
            return Response(
                "Unauthorized", 
                401,
                {"WWW-Authenticate": "Basic realm='Login Required'"}
            )
        return f(*args, **kwargs)
    return decorated

# Initialize the photo count
stored_photo_count = 0

@app.route("/transactions_review", methods=["GET"])
@requires_auth
def transactions_review_endpoint():
    try:
        count = get_review_count()
        return jsonify({"transactions_to_review": count}), 200
    except Exception as e:
        return jsonify({"error": f"Error fetching review count: {e}"}), 500

@app.route("/chase_balance", methods=["GET"])
@requires_auth
def chase_balance_endpoint():
    try:
        balance = asyncio.run(get_chase_balance())
        return jsonify({"chase_balance": balance}), 200
    except Exception as e:
        return jsonify({"error": f"Error fetching Chase balance: {e}"}), 500

@app.route("/refresh_accounts", methods=["GET", "POST"])
@requires_auth
def refresh_accounts_endpoint():
    try:
        refresh_accounts()
        return jsonify({"status": "Accounts refreshed successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Error refreshing accounts: {e}"}), 500

@app.route("/food_log_count", methods=["GET", "POST"])
@requires_auth
def food_log_count_endpoint():
    global stored_photo_count
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        if "photo_count" not in data:
            return jsonify({"error": "Missing photo_count"}), 400
        try:
            stored_photo_count = int(data["photo_count"])
            return jsonify({"photo_count": stored_photo_count}), 200
        except ValueError:
            return jsonify({"error": "photo_count must be an integer"}), 400
    # GET
    return jsonify({"photo_count": stored_photo_count}), 200

if __name__ == "__main__":
    # Turn off the debugger in production; avoid emoji in logs
    app.run(host="0.0.0.0", port=5000, debug=False)