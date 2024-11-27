# app.py

from flask import Flask, jsonify
import asyncio
import logging
from scripts.get_chase_balance import get_chase_balance  # For getting the Chase balance
from scripts.refresh_accounts import refresh_accounts  # For refreshing accounts
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

# Get balance route
@app.route('/budgetcalendar/get-balance/', methods=['GET'])
def get_balance():
    try:
        balance = asyncio.run(get_chase_balance())
        if balance is not None:
            logging.info(f"Returning balance: {balance}")
            return jsonify({"balance": balance}), 200
        else:
            logging.error("Failed to retrieve balance.")
            return jsonify({"error": "Failed to retrieve balance"}), 500
    except Exception as e:
        logging.error(f"Exception occurred in get_balance route: {e}", exc_info=True)
        return jsonify({"error": f"Exception occurred: {e}"}), 500

# Refresh accounts route
@app.route('/budgetcalendar/refresh-accounts/', methods=['GET'])
def refresh_accounts_route():
    try:
        logging.info("Initiating account refresh...")
        refresh_accounts()
        logging.info("Account refresh completed successfully.")
        return jsonify({"status": "Accounts refreshed successfully"}), 200
    except Exception as e:
        logging.error(f"Exception occurred in refresh_accounts_route: {e}", exc_info=True)
        return jsonify({"error": f"Failed to refresh accounts: {e}"}), 500

# Removed execute route as it references a non-existent module

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5003))  # Default to port 5003 if not set
    app.run(host="0.0.0.0", port=port)