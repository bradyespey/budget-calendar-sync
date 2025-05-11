# scripts/refresh_accounts.py

import os
import time
import json
import sys
import tempfile
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# ── Configuration ─────────────────────────────────────────────────────────
USE_HEADLESS     = False  # True → headless, False → GUI
COOKIES_FILE     = r"C:\Projects\Budget\monarch_cookies.json"
LOGIN_URL        = "https://app.monarchmoney.com/login"
DASHBOARD_URL    = "https://app.monarchmoney.com/dashboard"
ACCOUNTS_URL     = "https://app.monarchmoney.com/accounts"
CHROMEDRIVER_EXE = r"C:\Drivers\Chrome\chromedriver.exe"

# ── Helpers ──────────────────────────────────────────────────────────────
def load_cookies(driver) -> bool:
    """Load saved cookies into the WebDriver session."""
    if not os.path.exists(COOKIES_FILE):
        print("Cookies file not found. Run save_cookies.py first.")
        return False
    with open(COOKIES_FILE, "r") as f:
        cookies = json.load(f)
    for c in cookies:
        if "expiry" in c:
            c["expiry"] = int(c["expiry"])
        try:
            driver.add_cookie(c)
        except Exception as exc:
            print(f"Error adding cookie: {exc}")
    return True

# ── Core Refresh Function ─────────────────────────────────────────────────
def refresh_accounts() -> bool:
    """Refresh Monarch accounts; return True on success, False on failure."""
    # Always give Chrome its own temp profile to avoid lockfile collisions
    profile_dir = tempfile.mkdtemp(prefix="monarch_tmp_")
    extra_args  = ["--headless=new"] if USE_HEADLESS else []
    print(f"Running in {'headless' if USE_HEADLESS else 'GUI'} mode.")

    # Chrome options
    opts = webdriver.ChromeOptions()
    opts.add_argument(f"--user-data-dir={profile_dir}")
    for arg in extra_args:
        opts.add_argument(arg)
    opts.add_argument("--start-maximized")
    opts.add_argument("--disable-logging")
    opts.add_argument("--log-level=3")

    # launch Chrome
    try:
        driver = webdriver.Chrome(service=Service(CHROMEDRIVER_EXE), options=opts)
    except Exception as exc:
        print(f"Error starting ChromeDriver: {exc}")
        return False

    try:
        # 1) Navigate to login so cookies attach to the right domain
        driver.get(LOGIN_URL)
        time.sleep(2)

        # 2) Load cookies
        if not load_cookies(driver):
            driver.quit()
            return False
        print("Loaded cookies.")

        # 3) Verify login
        driver.get(DASHBOARD_URL)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[@href='/accounts']"))
        )
        print("Login verified.")

        # 4) Click “Refresh all”
        driver.get(ACCOUNTS_URL)
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Refresh all']"))
        ).click()
        print("Clicked 'Refresh all'.")

        # 5) Wait for toaster confirmation
        WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located(
                (By.XPATH,
                 "//div[contains(@class,'Toaster') and .//span[contains(text(),'Refreshing your connections')]]")
            )
        )
        print("Refresh confirmed.")

        # 6) If GUI, hold the window open until user acknowledges
        if not USE_HEADLESS:
            input("✓ Done. Press <Enter> to close Chrome…")
        else:
            time.sleep(5)

    except Exception as exc:
        print(f"Refresh failed: {exc}")
        driver.quit()
        return False
    finally:
        driver.quit()

    return True

# ── CLI entry-point ───────────────────────────────────────────────────────
if __name__ == "__main__":
    sys.exit(0 if refresh_accounts() else 1)