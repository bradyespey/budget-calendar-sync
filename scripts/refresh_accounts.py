import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

def load_credentials(filepath):
    with open(filepath, 'r') as file:
        credentials = json.load(file)
    return credentials['email'], credentials['password']

# Selenium-based function to refresh Monarch accounts
def refresh_accounts():
    # Load credentials from the JSON file
    email, password = load_credentials("C:\\Projects\\BudgetCalendar\\credentials.json")

    # Setup Selenium ChromeDriver
    service = Service("C:\\WebDriver\\chromedriver.exe")  # Update with the path to your chromedriver if different
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")

    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        # Step 1: Navigate to the Monarch login page
        driver.get("https://app.monarchmoney.com/login")
        
        # Step 2: Wait for the login form to be visible
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "form"))
        )
        print("Login form is visible.")

        # Step 3: Perform login using tab navigation
        actions = webdriver.ActionChains(driver)

        # Tab 4 times to reach the email input field
        for _ in range(4):
            actions.send_keys(Keys.TAB).perform()
            time.sleep(0.5)  # Small delay between tabbing to ensure it works smoothly

        # Input email
        actions.send_keys(email).perform()
        time.sleep(1)

        # Tab once to reach the password field
        actions.send_keys(Keys.TAB).perform()
        time.sleep(0.5)

        # Input password
        actions.send_keys(password).perform()
        time.sleep(1)

        # Press Enter to submit the form
        actions.send_keys(Keys.ENTER).perform()

        # Step 4: Wait for the accounts element to confirm successful login
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//a[@href='/accounts']"))
        )
        print("Login successful, accounts link is visible.")

        # Step 5: Navigate to the accounts page
        driver.get("https://app.monarchmoney.com/accounts")
        time.sleep(5)

        # Step 6: Wait for the "Refresh all" button to be clickable
        refresh_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Refresh all']"))
        )
        refresh_button.click()
        print("Clicked the 'Refresh all' button.")
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()
