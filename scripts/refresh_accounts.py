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

# ── Configuration ────────────────────────────────────────────────────────
USE_HEADLESS     = False  # True → headless, False → GUI
COOKIES_FILE     = r"C:\Projects\Budget\monarch_cookies.json"
PROFILE_PATH     = r"C:\Projects\Budget\chrome_profile"
LOGIN_URL        = "https://app.monarchmoney.com/login"
DASHBOARD_URL    = "https://app.monarchmoney.com/dashboard"
ACCOUNTS_URL     = "https://app.monarchmoney.com/accounts"
CHROMEDRIVER_EXE = r"C:\Drivers\Chrome\chromedriver.exe"

# ── Helpers ──────────────────────────────────────────────────────────────
def ensure_profile_folder() -> None:
    """Create profile folder and remove stale lock file."""
    if not os.path.exists(PROFILE_PATH):
        os.makedirs(PROFILE_PATH)
        print(f"Created profile folder: {PROFILE_PATH}")
    lock_file = os.path.join(PROFILE_PATH, "SingletonLock")
    if os.path.exists(lock_file):
        try:
            os.remove(lock_file)
            print("Removed existing lock file.")
        except Exception as e:
            print(f"Could not remove lock file: {e}")


def load_cookies(driver) -> bool:
    """Load saved cookies into the WebDriver session."""
    if not os.path.exists(COOKIES_FILE):
        print("Cookies file not found. Run save_cookies.py first.")
        return False
    with open(COOKIES_FILE, "r") as f:
        cookies = json.load(f)
    for cookie in cookies:
        if "expiry" in cookie:
            cookie["expiry"] = int(cookie["expiry"])
        try:
            driver.add_cookie(cookie)
        except Exception as e:
            print(f"Error adding cookie: {e}")
    return True

# ── Main Refresh Function ─────────────────────────────────────────────────
def refresh_accounts() -> bool:
    """Refresh Monarch accounts; return True on success, False on failure."""
    ensure_profile_folder()

    # choose profile directory and headless args
    if USE_HEADLESS:
        profile_dir = tempfile.mkdtemp(prefix="monarch_tmp_")
        chrome_args = ["--headless=new"]
        print("Running in headless mode.")
    else:
        profile_dir = PROFILE_PATH
        chrome_args = []
        print("Running in GUI mode.")

    # set up Chrome options
    opts = webdriver.ChromeOptions()
    opts.add_argument(f"--user-data-dir={profile_dir}")
    for arg in chrome_args:
        opts.add_argument(arg)
    opts.add_argument("--start-maximized")
    opts.add_argument("--disable-logging")
    opts.add_argument("--log-level=3")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")

    # launch Chrome
    try:
        driver = webdriver.Chrome(service=Service(CHROMEDRIVER_EXE), options=opts)
    except Exception as e:
        print(f"Error starting ChromeDriver: {e}")
        return False

    try:
        # 1) Navigate to login to attach cookies
        driver.get(LOGIN_URL)
        time.sleep(2)

        # 2) Load cookies and verify
        if not load_cookies(driver):
            driver.quit()
            return False
        print("Loaded cookies.")

        # 3) Verify login
        driver.get(DASHBOARD_URL)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[@href='/accounts']"))
        )
        print("Logged in using persistent cookies.")

        # 4) Click "Refresh all"
        driver.get(ACCOUNTS_URL)
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Refresh all']"))
        ).click()
        print("Clicked the 'Refresh all' button.")

        # 5) Wait for confirmation toaster
        WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located(
                (By.XPATH,
                 "//div[contains(@class,'Toaster') and .//span[contains(text(),'Refreshing your connections')]]")
            )
        )
        print("Refresh confirmed by toaster message.")

        # 6) Allow finalization
        time.sleep(5)
    except Exception as e:
        print(f"An error occurred during refresh: {e}")
        driver.quit()
        return False
    finally:
        driver.quit()

    return True

# ── Execution Entry ────────────────────────────────────────────────────────
if __name__ == "__main__":
    ok = refresh_accounts()
    if not ok:
        print("Account refresh FAILED.")
        sys.exit(1)
    print("Account refresh SUCCEEDED.")
