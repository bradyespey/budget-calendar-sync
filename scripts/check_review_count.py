# scripts/check_review_count.py

import os
import time
import json
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# Always run in non-headless mode for testing.
USE_HEADLESS = True
COOKIES_FILE = "C:\\Repos\\budget-calendar-sync\\monarch_cookies.json"
# Persistent profile folder for Chrome (adjust the path as needed)
PROFILE_PATH = "C:\\Repos\\budget-calendar-sync\\chrome_profile"
DASHBOARD_URL = "https://app.monarchmoney.com/dashboard"
TRANSACTIONS_URL = "https://app.monarchmoney.com/transactions?needsReview=true&needsReviewUnassigned=true"

def ensure_profile_folder():
    if not os.path.exists(PROFILE_PATH):
        os.makedirs(PROFILE_PATH)
        print(f"Created profile folder: {PROFILE_PATH}")
    # Remove potential Chrome lock files
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
            if "expiry" in cookie:
                cookie["expiry"] = int(cookie["expiry"])
            try:
                driver.add_cookie(cookie)
            except Exception as e:
                print("Error adding cookie:", e)

def get_review_count():
    if not os.path.exists(COOKIES_FILE):
        print("Cookie file not found. Please run save_cookies.py first.")
        return None

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
        return None

    review_count = 0

    try:
        # Navigate to the login page (to ensure correct domain for cookies)
        driver.get("https://app.monarchmoney.com/login")
        time.sleep(3)
        
        # Load cookies from file
        load_cookies(driver)
        print("Loaded cookies from file.")
        time.sleep(2)
        
        # Navigate to the dashboard to verify login
        driver.get(DASHBOARD_URL)
        time.sleep(3)
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//a[@href='/accounts']"))
            )
            print("Logged in using persistent profile and cookies.")
        except Exception:
            print("Login verification failed using cookies. Please re-run save_cookies.py.")
            driver.quit()
            return None

        # Navigate to the transactions review page
        driver.get(TRANSACTIONS_URL)
        time.sleep(5)
        # Locate the "Mark all XXX as reviewed" button
        review_button = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '//button[contains(text(), "Mark all")]'))
        )
        button_text = review_button.text
        print(f"Button text found: {button_text}")
        # Parse the review count from the button text
        match = re.search(r"Mark all (\d+) as reviewed", button_text)
        if match:
            review_count = int(match.group(1))
        else:
            print("Could not parse the review count from the button text.")
    except Exception as e:
        print("Error:", e)
        driver.quit()
        return None
    finally:
        driver.quit()

    return review_count

if __name__ == "__main__":
    count = get_review_count()
    if count is not None:
        print("Number of transactions needing review:", count)