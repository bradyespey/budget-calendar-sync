# scripts/refresh_accounts.py

import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

def load_credentials():
    email = os.getenv("MONARCH_EMAIL")
    password = os.getenv("MONARCH_PASSWORD")
    if not email or not password:
        logging.error("Environment variables MONARCH_EMAIL and MONARCH_PASSWORD must be set.")
        raise ValueError("Environment variables MONARCH_EMAIL and MONARCH_PASSWORD must be set.")
    return email, password

# Selenium-based function to refresh Monarch accounts
def refresh_accounts():
    email, password = load_credentials()
    driver = None  # Initialize driver variable

    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode for Heroku
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")  # Optional: Define window size
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")

    # Set binary location from Heroku's environment variable
    chrome_bin = os.environ.get("GOOGLE_CHROME_BIN", "/app/.apt/usr/bin/google-chrome")
    options.binary_location = chrome_bin

    try:
        # Initialize WebDriver using webdriver-manager
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        logging.info("ChromeDriver initialized successfully.")

        # Step 1: Navigate to the Monarch login page
        driver.get("https://app.monarchmoney.com/login")
        logging.info("Navigated to Monarch login page.")

        # Step 2: Wait for the login form to be visible
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "form"))
        )
        logging.info("Login form is visible.")

        # Step 3: Perform login using direct element access
        driver.find_element(By.ID, "email").send_keys(email)
        driver.find_element(By.ID, "password").send_keys(password)
        driver.find_element(By.ID, "submit-button").click()
        logging.info("Submitted login form.")

        # Step 4: Wait for the accounts element to confirm successful login
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//a[@href='/accounts']"))
        )
        logging.info("Login successful, accounts link is visible.")

        # Step 5: Navigate to the accounts page
        driver.get("https://app.monarchmoney.com/accounts")
        logging.info("Navigated to accounts page.")
        time.sleep(5)  # Wait for the page to load

        # Step 6: Wait for the "Refresh all" button to be clickable and click it
        refresh_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Refresh all']"))
        )
        refresh_button.click()
        logging.info("Clicked the 'Refresh all' button.")
        
    except Exception as e:
        logging.error(f"An error occurred during account refresh: {e}", exc_info=True)
        raise e  # Re-raise exception to be caught in app.py
    finally:
        if driver:
            driver.quit()
            logging.info("ChromeDriver session ended.")