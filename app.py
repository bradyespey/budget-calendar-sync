# app.py

from flask import Flask, jsonify, request
import asyncio
import logging
from scripts.get_chase_balance import get_chase_balance
from scripts.refresh_accounts import refresh_accounts
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

@app.before_request
def log_request_info():
    logging.info(f"Received {request.method} request at {request.path}")

@app.route("/budgetcalendar/get-balance/", methods=["GET"])
def get_balance_route():
    try:
        balance = asyncio.run(get_chase_balance())
        if balance:
            logging.info(f"Returning balance: {balance}")
            return jsonify({"balance": balance})
        else:
            logging.error("Failed to retrieve balance.")
            return jsonify({"error": "Failed to retrieve balance"}), 500
    except Exception as e:
        logging.error(f"Exception occurred in get_balance_route: {e}")
        return jsonify({"error": f"Exception occurred: {e}"}), 500

@app.route("/budgetcalendar/refresh-accounts/", methods=["GET"])
def refresh_accounts_route():
    try:
        refresh_accounts()
        logging.info("Accounts refreshed successfully.")
        return jsonify({"status": "Accounts refreshed successfully!"})
    except Exception as e:
        logging.error(f"Exception occurred in refresh_accounts_route: {e}")
        return jsonify({"error": f"Failed to refresh accounts: {e}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Heroku assigns the PORT
    app.run(host="0.0.0.0", port=port, debug=False)