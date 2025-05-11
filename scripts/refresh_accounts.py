# scripts/refresh_accounts.py

import os, sys, time, json, tempfile
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# ── Config ───────────────────────────────────────────────────────────────
USE_HEADLESS = True
if __name__ == "__main__":
    USE_HEADLESS = False
COOKIES_FILE     = r"C:\Projects\Budget\monarch_cookies.json"
PROFILE_PATH     = r"C:\Projects\Budget\chrome_profile"
LOGIN_URL        = "https://app.monarchmoney.com/login"
DASHBOARD_URL    = "https://app.monarchmoney.com/dashboard"
ACCOUNTS_URL     = "https://app.monarchmoney.com/accounts"
CHROMEDRIVER_EXE = r"C:\Drivers\Chrome\chromedriver.exe"

# ── Helpers ───────────────────────────────────────────────────────────────
def ensure_profile_folder():
    if not os.path.exists(PROFILE_PATH):
        os.makedirs(PROFILE_PATH)
    lock = os.path.join(PROFILE_PATH, "SingletonLock")
    if os.path.exists(lock):
        os.remove(lock)

def load_cookies(driver):
    if not os.path.exists(COOKIES_FILE):
        print("cookie file missing – run save_cookies.py first")
        return False
    with open(COOKIES_FILE) as f:
        cookies = json.load(f)
    for c in cookies:
        if "expiry" in c:
            c["expiry"] = int(c["expiry"])
        driver.add_cookie(c)
    driver.refresh()
    time.sleep(1)
    return True

# ── Refresh Routine ───────────────────────────────────────────────────────
def refresh_accounts():
    ensure_profile_folder()
    opts = webdriver.ChromeOptions()
    opts.add_argument(f"--user-data-dir={PROFILE_PATH}")
    if USE_HEADLESS:
        opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--start-maximized")
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])

    try:
        driver = webdriver.Chrome(service=Service(CHROMEDRIVER_EXE), options=opts)
    except Exception as e:
        print("ChromeDriver error:", e)
        return False

    try:
        driver.get(LOGIN_URL)                              # open login
        time.sleep(2)
        if not load_cookies(driver):                       # inject cookies
            driver.quit()
            return False
        driver.get(DASHBOARD_URL)                          # verify login
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[@href='/accounts']"))
        )
        driver.get(ACCOUNTS_URL)                           # navigate to accounts
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Refresh all']"))
        ).click()
        return True                                       # clicked, return
    except Exception as e:
        print("Refresh failed:", e)
        return False
    finally:
        driver.quit()

# ── CLI Entry ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    sys.exit(0 if refresh_accounts() else 1)