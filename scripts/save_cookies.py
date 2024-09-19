##############################################################################################################################
# Make sure Chrome is not running and the 'C:\Projects\BudgetCalendar\chrome_profile' directory is deleted before running this script.
##############################################################################################################################

import json
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import InvalidSessionIdException, WebDriverException

# Set up paths and URLs
cookie_path = "C:\\Projects\\BudgetCalendar\\monarch_cookies.json"
profile_path = "C:\\Projects\\BudgetCalendar\\chrome_profile"
url = "https://app.monarchmoney.com/login"

# Set up ChromeDriver with a persistent profile
service = Service("C:\\WebDriver\\chromedriver.exe")
options = webdriver.ChromeOptions()
options.add_argument(f"user-data-dir={profile_path}")
options.add_argument("--start-maximized")  # Open in maximized window
options.add_argument("--disable-logging")  # Suppress logging
options.add_argument("--log-level=3")      # Suppress verbose logs

try:
    # Initialize the WebDriver
    driver = webdriver.Chrome(service=service, options=options)

    # Navigate to the website
    driver.get(url)

    # Wait for 60 seconds to allow manual login
    delay = 60  # 60 seconds
    print(f"Please log in to Monarch Money manually. Waiting for {delay} seconds...")
    time.sleep(delay)  # Wait for the user to log in

    # Save the cookies after login
    if not os.path.exists(os.path.dirname(cookie_path)):
        os.makedirs(os.path.dirname(cookie_path))  # Create directory if it doesn't exist
        print(f"Created directory: {os.path.dirname(cookie_path)}")

    # Retrieve and save the cookies
    cookies = driver.get_cookies()
    print(f"Retrieved cookies: {cookies}")  # Debugging: Print cookies

    with open(cookie_path, "w") as cookie_file:
        json.dump(cookies, cookie_file)
    print(f"Cookies saved to {cookie_path}")

except WebDriverException as e:
    print(f"WebDriverException occurred: {e}")
except InvalidSessionIdException as e:
    print(f"Session invalid or no longer exists: {e}")
except Exception as e:
    print(f"An error occurred: {type(e).__name__}, {e}")
finally:
    driver.quit()
