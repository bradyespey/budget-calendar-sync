from flask import Flask, jsonify
import asyncio
from scripts.get_chase_balance import get_chase_balance  # For getting the Chase balance
from scripts.refresh_accounts import refresh_accounts  # For refreshing accounts

app = Flask(__name__)

# Get balance route
@app.route('/budgetcalendar/get-balance/', methods=['GET'])
def get_balance():
    balance = asyncio.run(get_chase_balance())
    if balance:
        return jsonify({"balance": balance})
    else:
        return jsonify({"error": "Failed to retrieve balance"}), 500

# Refresh accounts route
@app.route('/budgetcalendar/refresh-accounts/', methods=['GET'])
def refresh_accounts_only():
    try:
        refresh_accounts()
        return jsonify({"status": "Accounts refreshed successfully"})
    except Exception as e:
        return jsonify({"error": f"Failed to refresh accounts: {e}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)
