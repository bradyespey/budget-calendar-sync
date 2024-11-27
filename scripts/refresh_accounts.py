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
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")  # Optional: Define window size
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")

    # Set binary location from Heroku's environment variable
    chrome_bin = "/app/.chrome-for-testing/chrome-linux64/chrome"
    options.binary_location = chrome_bin

    try:
        # Initialize WebDriver using the new chromedriver path
        chromedriver_path = "/app/.chrome-for-testing/chromedriver-linux64/chromedriver"
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=options)
        logging.info("ChromeDriver initialized successfully.")

        # Step 1: Navigate to the Monarch login page
        driver.get("https://app.monarchmoney.com/login")
        logging.info("Navigated to Monarch login page.")

        # Log the page title to verify navigation
        logging.info(f"Page title: {driver.title}")

        # Step 2: Wait for the login form to be visible
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "form"))
            )
            logging.info("Login form is visible.")
        except Exception as e:
            logging.error("Login form not found.")
            logging.debug(driver.page_source)
            raise

        # Step 3: Perform login using direct element access
        # Attempt to locate the email input field
        try:
            email_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            logging.info("Email input field found by ID.")
        except:
            # Try alternative locator by NAME
            try:
                email_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "email"))
                )
                logging.info("Email input field found by NAME.")
            except:
                logging.error("Unable to locate the email input field.")
                logging.debug(driver.page_source)
                raise

        email_input.send_keys(email)
        logging.info("Entered email.")

        # Attempt to locate the password input field
        try:
            password_input = driver.find_element(By.ID, "password")
            logging.info("Password input field found by ID.")
        except:
            # Try alternative locator by NAME
            try:
                password_input = driver.find_element(By.NAME, "password")
                logging.info("Password input field found by NAME.")
            except:
                logging.error("Unable to locate the password input field.")
                logging.debug(driver.page_source)
                raise

        password_input.send_keys(password)
        logging.info("Entered password.")

        # Submit the form
        password_input.send_keys(Keys.RETURN)
        logging.info("Submitted login form.")

        # Step 4: Wait for the accounts element to confirm successful login
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, "//a[@href='/accounts']"))
            )
            logging.info("Login successful, accounts link is visible.")
        except Exception as e:
            logging.error("Login may have failed, accounts link not found.")
            logging.debug(driver.page_source)
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
        except Exception as e:
            logging.error("Unable to locate or click the 'Refresh all' button.")
            logging.debug(driver.page_source)
            raise

    except Exception as e:
        logging.error(f"An error occurred during account refresh: {e}", exc_info=True)
        raise e  # Re-raise exception to be caught in app.py
    finally:
        if driver:
            driver.quit()
            logging.info("ChromeDriver session ended.")

# Allow the script to be run directly
if __name__ == "__main__":
    refresh_accounts()