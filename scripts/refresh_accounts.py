# scripts/refresh_accounts.py

import os
import sys
import asyncio
from dotenv import load_dotenv
from monarchmoney import MonarchMoney

# Load .env from project root
env_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, ".env")
)
load_dotenv(dotenv_path=env_path)

async def _refresh():
    email    = os.getenv("MONARCH_EMAIL")
    password = os.getenv("MONARCH_PASSWORD")
    mfa_key  = os.getenv("MONARCH_MFA_SECRET")

    if not all([email, password, mfa_key]):
        raise ValueError("Set MONARCH_EMAIL, MONARCH_PASSWORD, and MONARCH_MFA_SECRET in .env")

    mm = MonarchMoney()
    # login with TOTP seed
    await mm.login(
        email=email,
        password=password,
        mfa_secret_key=mfa_key,
        save_session=True,
        use_saved_session=False
    )
    # **await** the coroutine here:
    await mm.request_accounts_refresh_and_wait()

def refresh_accounts():
    asyncio.run(_refresh())

if __name__ == "__main__":
    try:
        print("Requesting account refresh…")
        refresh_accounts()
        print("Account refresh complete.")
    except Exception as e:
        print(f"Account refresh FAILED: {e}", file=sys.stderr)
        sys.exit(1)
    sys.exit(0)
