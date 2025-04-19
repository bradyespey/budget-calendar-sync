# scripts/save_cookies.py

import json
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException

# Path where cookies will be saved
COOKIE_PATH = "C:\\Projects\\Budget\\monarch_cookies.json"
# Persistent Chrome profile folder (this stores cookies, localStorage, etc.)
PROFILE_PATH = "C:\\Projects\\Budget\\chrome_profile"
# URL for Monarch login
LOGIN_URL = "https://app.monarchmoney.com/login"

# Set up ChromeDriver options (always non-headless for manual login)
options = webdriver.ChromeOptions()
options.add_argument(f"user-data-dir={PROFILE_PATH}")
options.add_argument("--start-maximized")
options.add_argument("--disable-logging")
options.add_argument("--log-level=3")

service = Service("C:\\Drivers\\WebDriver\\chromedriver.exe")
driver = webdriver.Chrome(service=service, options=options)

try:
    driver.get(LOGIN_URL)
    print("Please log in to Monarch Money manually (including MFA) in the opened browser window.")
    input("Press Enter after you have successfully logged in and the dashboard is visible...")
    
    # Retrieve cookies after successful login
    cookies = driver.get_cookies()
    cookie_dir = os.path.dirname(COOKIE_PATH)
    if not os.path.exists(cookie_dir):
        os.makedirs(cookie_dir)
        print(f"Created directory: {cookie_dir}")
    
    with open(COOKIE_PATH, "w") as cookie_file:
        json.dump(cookies, cookie_file)
    print(f"Cookies saved to {COOKIE_PATH}")
except WebDriverException as e:
    print(f"WebDriverException occurred: {e}")
except Exception as e:
    print(f"An error occurred: {type(e).__name__}, {e}")
finally:
    driver.quit()