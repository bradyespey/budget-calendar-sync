# scripts/refresh_accounts.py

import os
import time
import logging
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

# ======= TOGGLE OPTIONS =======
HEADLESS_MODE = True  # Set to True for headless mode, False for visible Chrome
# =============================

# Load environment variables from .env
load_dotenv()

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

def load_credentials():
    """
    Load credentials from environment variables if running on Heroku,
    otherwise load from a local JSON file.
    """
    # Determine if running on Heroku by checking for the 'DYNO' environment variable
    IS_HEROKU = 'DYNO' in os.environ
    logging.info(f"IS_HEROKU: {IS_HEROKU}")  # Log environment detection

    if IS_HEROKU:
        email = os.getenv("MONARCH_EMAIL")
        password = os.getenv("MONARCH_PASSWORD")
        if not email or not password:
            logging.error("Environment variables MONARCH_EMAIL and MONARCH_PASSWORD must be set on Heroku.")
            raise ValueError("Environment variables MONARCH_EMAIL and MONARCH_PASSWORD must be set.")
    else:
        # Load credentials from a local JSON file
        # Dynamically set the path to credentials.json relative to this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        filepath = os.path.join(script_dir, "../credentials.json")
        logging.info(f"Looking for credentials at: {filepath}")  # Log the filepath

        try:
            with open(filepath, 'r') as file:
                credentials = json.load(file)
            email = credentials.get('email')
            password = credentials.get('password')

            if not email or not password:
                logging.error("Email or password not found in the credentials.json file.")
                raise ValueError("Email or password not found in the credentials.json file.")
        except FileNotFoundError:
            logging.error(f"Credentials file not found at path: {filepath}")
            raise
        except json.JSONDecodeError:
            logging.error("Error decoding the credentials.json file. Ensure it is valid JSON.")
            raise

    return email, password

def refresh_accounts():
    """
    Selenium-based function to refresh Monarch accounts.
    """
    email, password = load_credentials()
    driver = None  # Initialize driver variable

    # Configure Chrome options
    options = webdriver.ChromeOptions()
    if HEADLESS_MODE:
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")  # Often needed for headless Chrome
        options.add_argument("--no-sandbox")   # Bypass OS security model
        options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
    options.add_argument("--window-size=1920,1080")  # Optional: Define window size
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")

    # Add user-agent to mimic a real browser
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/115.0.0.0 Safari/537.36")

    # Determine if running on Heroku
    IS_HEROKU = 'DYNO' in os.environ

    if IS_HEROKU:
        # Set Chrome binary location from Heroku's buildpack
        # These paths depend on the buildpacks used; adjust if necessary
        chrome_binary = "/app/.apt/usr/bin/google-chrome"  # Example path; verify with your buildpack
        chromedriver_path = "/app/.chromedriver/bin/chromedriver"  # Example path; verify with your buildpack

        options.binary_location = chrome_binary
        logging.info(f"Using Chrome binary at: {chrome_binary}")
        logging.info(f"Using Chromedriver at: {chromedriver_path}")
    else:
        # Use webdriver-manager to handle Chromedriver installation locally
        chromedriver_path = ChromeDriverManager().install()
        logging.info(f"Using Chromedriver from webdriver-manager at: {chromedriver_path}")

    try:
        # Initialize WebDriver
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=options)
        logging.info("ChromeDriver initialized successfully.")

        # Step 1: Navigate to the Monarch login page
        driver.get("https://app.monarchmoney.com/login")
        logging.info("Navigated to Monarch login page.")

        # Optional: Log the page title to verify navigation
        logging.info(f"Page title: {driver.title}")

        # Step 2: Wait for the login form to be visible
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "form"))
            )
            logging.info("Login form is visible.")
        except Exception:
            logging.error("Login form not found.")
            # Take a screenshot for debugging
            driver.save_screenshot('login_page.png')
            raise

        # Step 3: Perform login using tab navigation
        actions = ActionChains(driver)

        # Tab 4 times to reach the email input field
        for _ in range(4):
            actions.send_keys(Keys.TAB).perform()
            time.sleep(0.5)  # Small delay between tabbing to ensure it works smoothly

        # Input email
        actions.send_keys(email).perform()
        logging.info("Entered email.")
        time.sleep(1)

        # Tab once to reach the password field
        actions.send_keys(Keys.TAB).perform()
        time.sleep(0.5)

        # Input password
        actions.send_keys(password).perform()
        logging.info("Entered password.")
        time.sleep(1)

        # Press Enter to submit the form
        actions.send_keys(Keys.ENTER).perform()
        logging.info("Submitted login form.")

        # Step 4: Wait for the accounts element to confirm successful login
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, "//a[@href='/accounts']"))
            )
            logging.info("Login successful, accounts link is visible.")
        except Exception:
            logging.error("Login may have failed, accounts link not found.")
            # Take a screenshot for debugging
            driver.save_screenshot('after_login.png')
            raise

        # Step 5: Navigate to the accounts page
        driver.get("https://app.monarchmoney.com/accounts")
        logging.info("Navigated to accounts page.")
        time.sleep(5)  # Wait for the page to load

        # Step 6: Wait for the "Refresh all" button to be clickable and click it
        try:
            refresh_button = WebDriverWait(driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, "//span[text()='Refresh all']"))
            )
            refresh_button.click()
            logging.info("Clicked the 'Refresh all' button.")
        except Exception:
            logging.error("Unable to locate or click the 'Refresh all' button.")
            # Take a screenshot for debugging
            driver.save_screenshot('accounts_page.png')
            raise

    except Exception as e:
        logging.error(f"An error occurred during account refresh: {e}", exc_info=True)
        raise e  # Re-raise exception to be caught in app.py or for debugging
    finally:
        if driver:
            driver.quit()
            logging.info("ChromeDriver session ended.")

# Allow the script to be run directly
if __name__ == "__main__":
    refresh_accounts()