import time
import os
import warnings
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.CRITICAL, format='%(message)s')

# Paths and URLs
url_login = "https://app.monarchmoney.com/login"
url_accounts = "https://app.monarchmoney.com/accounts"

# Hardcoded Monarch Money credentials
email = "baespey@gmail.com"
password = "gHn63sUR$S5!qxgI"

def initialize_driver():
    # Terminate any existing Chrome or ChromeDriver processes (Optional)
    os.system("taskkill /im chrome.exe /f >nul 2>&1")
    os.system("taskkill /im chromedriver.exe /f >nul 2>&1")

    # Use the manually downloaded ChromeDriver
    chrome_driver_path = "C:\\WebDriver\\chromedriver.exe"

    # Initialize ChromeDriver using the specified path
    service = Service(executable_path=chrome_driver_path)
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")

    driver = webdriver.Chrome(service=service, options=options)
    
    return driver

def login(driver, email, password):
    driver.get(url_login)
    time.sleep(3)  # Allow the page to load

    try:
        # Tab 4 times to focus the email field
        body = driver.find_element(By.TAG_NAME, 'body')
        body.send_keys(Keys.TAB * 4)
        time.sleep(1)  # Ensure the email field is focused

        # Directly find the email field again to ensure focus, then enter the email
        email_field = driver.switch_to.active_element
        email_field.send_keys(email)
        time.sleep(1)

        # Tab once to focus the password field
        body.send_keys(Keys.TAB)
        time.sleep(1)

        # Directly find the password field again to ensure focus, then enter the password
        password_field = driver.switch_to.active_element
        password_field.send_keys(password)
        time.sleep(1)

        # Press Enter to submit the form
        password_field.send_keys(Keys.ENTER)

        time.sleep(5)  # Allow time for the login to process
    except Exception as e:
        print(f"Login failed: {e}")

def click_refresh_all_button(driver):
    try:
        # Wait for the 'Refresh all' button to be present
        refresh_all_button = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//button[contains(., 'Refresh all')]"))
        )
        
        # Scroll the button into view and click it
        driver.execute_script("arguments[0].scrollIntoView(true);", refresh_all_button)
        refresh_all_button.click()

        print("Clicked the 'Refresh all' button.")
        time.sleep(3)  # Give time for the refresh action to complete
    except Exception as e:
        print(f"Failed to click the 'Refresh all' button: {e}")

def main():
    driver = initialize_driver()

    try:
        # Log in to Monarch Money
        login(driver, email, password)
        
        # Check if login was successful
        if "login" in driver.current_url:
            print("Login failed. Please check your credentials.")
        else:
            print("Logged in successfully.")
            driver.get(url_accounts)
            time.sleep(3)  # Allow the accounts page to load

            # Click the 'Refresh all' button to sync all accounts
            click_refresh_all_button(driver)

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
