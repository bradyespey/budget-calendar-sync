# scripts/refresh_accounts.py

import os
import time
import json
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# Configuration
USE_HEADLESS     = True
COOKIES_FILE     = r"C:\Projects\Budget\monarch_cookies.json"
PROFILE_PATH     = r"C:\Projects\Budget\chrome_profile"
LOGIN_URL        = "https://app.monarchmoney.com/login"
DASHBOARD_URL    = "https://app.monarchmoney.com/dashboard"
ACCOUNTS_URL     = "https://app.monarchmoney.com/accounts"
CHROMEDRIVER_EXE = r"C:\Drivers\Chrome\chromedriver.exe"

def ensure_profile_folder():
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

def load_cookies(driver):
    if not os.path.exists(COOKIES_FILE):
        print("Cookies file not found. Please run save_cookies.py first.")
        return False
    with open(COOKIES_FILE, "r") as f:
        cookies = json.load(f)
    for cookie in cookies:
        if "expiry" in cookie:
            cookie["expiry"] = int(cookie["expiry"])
        try:
            driver.add_cookie(cookie)
        except Exception as e:
            print("Error adding cookie:", e)
    return True

def refresh_accounts():
    """Returns True if refresh succeeded, False otherwise."""
    ensure_profile_folder()

    options = webdriver.ChromeOptions()
    # use a clean profile so cookies get written
    options.add_argument(f"--user-data-dir={PROFILE_PATH}")
    if USE_HEADLESS:
        options.add_argument("--headless")
        print("Running in headless mode.")
    else:
        print("Running in non-headless mode.")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")
    # These two often fix “failed to write prefs file”
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(CHROMEDRIVER_EXE)
    try:
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        print("Error starting ChromeDriver:", e)
        return False

    try:
        # 1) Navigate to login so cookies apply to the right domain
        driver.get(LOGIN_URL)
        time.sleep(2)

        # 2) Load cookies
        if not load_cookies(driver):
            driver.quit()
            return False
        print("Loaded cookies from file.")
        time.sleep(2)

        # 3) Verify login
        driver.get(DASHBOARD_URL)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[@href='/accounts']"))
        )
        print("Logged in using persistent cookies.")

        # 4) Go to accounts and click “Refresh all”
        driver.get(ACCOUNTS_URL)
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Refresh all']"))
        ).click()
        print("Clicked the 'Refresh all' button.")

        # 5) Wait for confirmation toaster
        WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located(
                (By.XPATH,
                 "//div[contains(@class,'DEPRECATED_Toaster__Message') and .//span[contains(text(),'Refreshing your connections')]]")
            )
        )
        print("Refresh confirmed by toaster message.")

        # 6) Give it a few more seconds to finish
        time.sleep(5)
    except Exception as e:
        print("An error occurred during refresh:", e)
        driver.quit()
        return False
    finally:
        driver.quit()

    return True

if __name__ == "__main__":
    ok = refresh_accounts()
    if not ok:
        print("Account refresh FAILED.")
        sys.exit(1)
    print("Account refresh SUCCEEDED.")