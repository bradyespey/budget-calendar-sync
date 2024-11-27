# scripts/refresh_accounts.py

import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# ======= TOGGLE OPTIONS =======
headless_mode = True  # Set to False if you want to see the browser window during local testing
# =============================

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

def refresh_accounts():
    email, password = load_credentials()

    options = webdriver.ChromeOptions()
    if headless_mode:
        options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")  # Optional: Define window size

    # Determine if running on Heroku
    is_heroku = os.environ.get("DYNO") is not None

    try:
        if is_heroku:
            # Heroku uses an ephemeral filesystem; cache webdriver in /tmp
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager(cache_valid_range=1, path="/tmp/.wdm").install()),
                options=options
            )
        else:
            # Local environment
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

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
        logging.error(f"An error occurred: {e}")
    finally:
        driver.quit()
        logging.info("ChromeDriver session ended.")

if __name__ == "__main__":
    refresh_accounts()