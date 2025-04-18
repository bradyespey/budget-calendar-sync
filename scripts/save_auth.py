# scripts/save_auth.py

import json
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException

# Configuration paths
TOKEN_PATH = "C:\\Repos\\budget-calendar-sync\\monarch_token.json"
PROFILE_PATH = "C:\\Repos\\budget-calendar-sync\\chrome_profile"
LOGIN_URL = "https://app.monarchmoney.com/login"
CHROMEDRIVER_PATH = "C:\\Drivers\\chromedriver-win64\\chromedriver.exe"

options = webdriver.ChromeOptions()
options.add_argument(f"user-data-dir={PROFILE_PATH}")
options.add_argument("--start-maximized")
options.add_argument("--disable-logging")
options.add_argument("--log-level=3")

service = Service(CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service, options=options)

try:
    driver.get(LOGIN_URL)
    print("Please log in to Monarch Money manually (including MFA) in the opened browser window.")
    input("Press Enter after you have successfully logged in and the dashboard is visible...")

    # Extract persist:root from localStorage (which holds a JSON string)
    persist_root = driver.execute_script("return window.localStorage.getItem('persist:root');")
    if persist_root:
        data = json.loads(persist_root)
        # The 'user' key itself is a JSON string, so parse it further:
        user_data = json.loads(data.get("user", "{}"))
        token = user_data.get("token")
        if token:
            print("Extracted token:", token)
            # Save the token to a JSON file
            with open(TOKEN_PATH, "w") as f:
                json.dump({"token": token}, f)
            print(f"Token saved to {TOKEN_PATH}")
        else:
            print("Token not found in the user data.")
    else:
        print("persist:root not found in localStorage.")
except WebDriverException as e:
    print(f"WebDriverException occurred: {e}")
except Exception as e:
    print(f"An error occurred: {type(e).__name__}, {e}")
finally:
    driver.quit()