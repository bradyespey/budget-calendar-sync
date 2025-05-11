# app.py

import os
import sys
from threading import Thread
from functools import wraps

from flask import Flask, jsonify, request, Response, make_response
from flask_cors import CORS
from dotenv import load_dotenv

# ── Your job scripts ───────────────────────────────────────────────────────
from scripts.refresh_accounts import refresh_accounts
from scripts.get_chase_balance import get_chase_balance_async as _chase
from scripts.check_review_count import get_review_count as _rcount

# ── Env + Basic-Auth config ─────────────────────────────────────────────────
load_dotenv()
API_AUTH = os.getenv("API_AUTH", "")
if ":" not in API_AUTH:
    raise RuntimeError("API_AUTH must be set in the environment as 'user:pass'")
USER, PASS = API_AUTH.split(":", 1)

def _check(u: str, p: str) -> bool:
    return u == USER and p == PASS

# ── Flask + CORS setup ─────────────────────────────────────────────────────
app = Flask(__name__)
CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    supports_credentials=True,
    allow_headers=["Authorization", "Content-Type"],
    methods=["GET", "POST", "OPTIONS"],
)

def requires_auth(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        # let preflight through
        if request.method == "OPTIONS":
            return make_response(("", 204))
        auth = request.authorization
        if not auth or not _check(auth.username, auth.password):
            return Response(
                "Unauthorized", 401,
                {"WWW-Authenticate": "Basic realm='Login Required'"}
            )
        return fn(*args, **kwargs)
    return wrapped

# ── /refresh_accounts ──────────────────────────────────────────────────────
@app.route("/refresh_accounts", methods=["GET", "POST", "OPTIONS"])
@requires_auth
def refresh_accounts_endpoint():
    """
    ?sync=1   → run synchronously (blocks until done)
    otherwise → spawn background thread, return 202 immediately
    """
    run_sync = request.args.get("sync") == "1"

    def _worker():
        ok = refresh_accounts()   # uses script’s own USE_HEADLESS toggle
        print(f"refresh_accounts() finished: {ok}")

    if run_sync:
        print("🔧 running refresh_accounts() synchronously for debugging")
        _worker()
        return jsonify({"status": "Sync run complete"}), 200
    else:
        print("🔄 kicked off refresh_accounts() in background thread")
        Thread(target=_worker, daemon=True).start()
        return jsonify({"status": "Refresh job started"}), 202

# ── /chase_balance ─────────────────────────────────────────────────────────
@app.route("/chase_balance", methods=["GET", "OPTIONS"])
@requires_auth
def chase_balance_endpoint():
    try:
        bal = _chase()
        return jsonify({"chase_balance": bal}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── /transactions_review ───────────────────────────────────────────────────
@app.route("/transactions_review", methods=["GET", "OPTIONS"])
@requires_auth
def transactions_review_endpoint():
    try:
        cnt = _rcount()
        return jsonify({"transactions_to_review": cnt}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── Entry point ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"[Flask] listening on :5000  (basic-auth user = {USER})")
    app.run(host="0.0.0.0", port=5000, debug=False)