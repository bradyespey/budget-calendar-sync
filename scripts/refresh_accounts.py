# scripts/refresh_accounts.py

import os
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# Configuration
USE_HEADLESS = True  # Set True for headless mode
COOKIES_FILE = "C:\\Repos\\budget-calendar-sync\\monarch_cookies.json"
PROFILE_PATH = "C:\\Repos\\budget-calendar-sync\\chrome_profile"
LOGIN_URL = "https://app.monarchmoney.com/login"
DASHBOARD_URL = "https://app.monarchmoney.com/dashboard"
ACCOUNTS_URL = "https://app.monarchmoney.com/accounts"

def ensure_profile_folder():
    if not os.path.exists(PROFILE_PATH):
        os.makedirs(PROFILE_PATH)
        print(f"Created profile folder: {PROFILE_PATH}")
    # Remove potential lock file
    lock_file = os.path.join(PROFILE_PATH, "SingletonLock")
    if os.path.exists(lock_file):
        try:
            os.remove(lock_file)
            print("Removed existing lock file.")
        except Exception as e:
            print(f"Could not remove lock file: {e}")

def load_cookies(driver):
    if os.path.exists(COOKIES_FILE):
        with open(COOKIES_FILE, "r") as f:
            cookies = json.load(f)
        for cookie in cookies:
            # Ensure expiry is an integer if present
            if "expiry" in cookie:
                cookie["expiry"] = int(cookie["expiry"])
            try:
                driver.add_cookie(cookie)
            except Exception as e:
                print("Error adding cookie:", e)
    else:
        print("Cookies file not found. Please run save_cookies.py first.")

def refresh_accounts():
    ensure_profile_folder()

    options = webdriver.ChromeOptions()
    options.add_argument(f"user-data-dir={PROFILE_PATH}")
    if USE_HEADLESS:
        options.add_argument("--headless")
        print("Running in headless mode.")
    else:
        print("Running in non-headless mode.")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")

    service = Service("C:\\Drivers\\WebDriver\\chromedriver.exe")
    try:
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        print("Error starting ChromeDriver:", e)
        return

    try:
        # Open login page and load cookies
        driver.get(LOGIN_URL)
        time.sleep(3)
        load_cookies(driver)
        print("Loaded cookies from file.")
        time.sleep(2)
        
        # Navigate to dashboard to verify login
        driver.get(DASHBOARD_URL)
        time.sleep(3)
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//a[@href='/accounts']"))
            )
            print("Logged in using persistent cookies.")
        except Exception:
            print("Login verification failed. Please re-run save_cookies.py.")
            driver.quit()
            return

        # Navigate to the accounts page
        driver.get(ACCOUNTS_URL)
        time.sleep(5)
        print("Navigated to accounts page.")
        
        # Wait for and click the "Refresh all" button
        refresh_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Refresh all']"))
        )
        refresh_button.click()
        print("Clicked the 'Refresh all' button.")
        
        # Wait for the toaster message that confirms refresh
        WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located(
                (By.XPATH, "//div[contains(@class, 'DEPRECATED_Toaster__Message') and .//span[contains(text(), 'Refreshing your connections')]]")
            )
        )
        print("Refresh confirmed by toaster message.")
        
        # Wait a few seconds to allow the process to complete
        time.sleep(10)
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    refresh_accounts()