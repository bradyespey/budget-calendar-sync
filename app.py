# app.py

import os
import sys
import asyncio
from functools import wraps
from threading import Thread

from flask import Flask, jsonify, request, Response, make_response
from flask_cors import CORS
from dotenv import load_dotenv

# ── Job imports ────────────────────────────────────────────────────────────
from scripts.check_review_count import get_review_count
from scripts.get_chase_balance import get_chase_balance_async
from scripts.refresh_accounts import refresh_accounts

# ── Env + Basic-Auth config ────────────────────────────────────────────────
load_dotenv()
API_AUTH = os.getenv("API_AUTH", "")
if ":" not in API_AUTH:
    raise RuntimeError("API_AUTH must be set in the environment as 'user:pass'")
USER, PASS = API_AUTH.split(":", 1)

def check_auth(u: str, p: str) -> bool:
    return u == USER and p == PASS

def requires_auth(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if request.method == "OPTIONS":
            return make_response(("", 204))
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return Response(
                "Unauthorized", 401,
                {"WWW-Authenticate": "Basic realm='Login Required'"}
            )
        return fn(*args, **kwargs)
    return wrapped

# ── Flask + CORS setup ────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app,
     resources={r"/*": {"origins": "*"}},
     supports_credentials=True,
     allow_headers=["Authorization", "Content-Type"],
     methods=["GET", "POST", "OPTIONS"])

# ── /transactions_review ───────────────────────────────────────────────────
@app.route("/transactions_review", methods=["GET", "OPTIONS"])
@requires_auth
def transactions_review_endpoint():
    try:
        count = get_review_count()
        return jsonify({"transactions_to_review": count}), 200
    except Exception as e:
        return jsonify({"error": f"Error fetching review count: {e}"}), 500

# ── /chase_balance ─────────────────────────────────────────────────────────
@app.route("/chase_balance", methods=["GET", "OPTIONS"])
@requires_auth
def chase_balance_endpoint():
    try:
        bal = asyncio.run(get_chase_balance_async())
        return jsonify({"chase_balance": bal}), 200
    except Exception as e:
        return jsonify({"error": f"Error fetching Chase balance: {e}"}), 500

# ── /refresh_accounts ──────────────────────────────────────────────────────
@app.route("/refresh_accounts", methods=["GET", "POST", "OPTIONS"])
@requires_auth
def refresh_accounts_endpoint():
    def _run() -> bool:
        ok = refresh_accounts()          # honours USE_HEADLESS
        print(f"refresh_accounts() finished: {ok}")
        return ok

    run_sync = request.args.get("sync") == "1"

    if run_sync:
        print("🔧 running refresh_accounts() synchronously")
        return (
            (jsonify({"status": "Accounts refreshed"}), 200)
            if _run()
            else (jsonify({"error": "Account refresh FAILED"}), 500)
        )

    # async (fire-and-forget)
    print("🔄 kicked off refresh_accounts() in background thread")
    Thread(target=_run, daemon=True).start()
    return jsonify({"status": "Refresh job started"}), 202

# ── /food_log_count ────────────────────────────────────────────────────────
stored_photo_count = 0

@app.route("/food_log_count", methods=["GET", "POST", "OPTIONS"])
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
    return jsonify({"photo_count": stored_photo_count}), 200

# ── Entry point ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"[Flask] listening on :5000  (basic-auth user = {USER})")
    app.run(host="0.0.0.0", port=5000, debug=False)