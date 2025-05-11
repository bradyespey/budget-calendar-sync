# scripts/save_cookies.py

import os
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException

# ── Configuration ───────────────────────────────────────────────────────
COOKIE_PATH       = r"C:\Projects\Budget\monarch_cookies.json"
PROFILE_PATH      = r"C:\Projects\Budget\chrome_profile"
LOGIN_URL         = "https://app.monarchmoney.com/login"
CHROMEDRIVER_PATH = r"C:\Drivers\Chrome\chromedriver.exe"

# ── Ensure target directory exists ────────────────────────────────────────
def ensure_dir_for(path: str) -> None:
    directory = os.path.dirname(path)
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory: {directory}")

# ── Initialize ChromeDriver ──────────────────────────────────────────────
def init_driver() -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    options.add_argument(f"--user-data-dir={PROFILE_PATH}")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")
    service = Service(CHROMEDRIVER_PATH)
    return webdriver.Chrome(service=service, options=options)

# ── Main routine ──────────────────────────────────────────────────────────
def main() -> None:
    try:
        driver = init_driver()
        driver.get(LOGIN_URL)
        print("Please log in to Monarch Money (including MFA) in the opened browser.")
        input("Press Enter once you see your dashboard…")

        cookies = driver.get_cookies()
        ensure_dir_for(COOKIE_PATH)
        with open(COOKIE_PATH, "w", encoding="utf-8") as f:
            json.dump(cookies, f, indent=2)
        print(f"Saved {len(cookies)} cookies to {COOKIE_PATH}")

    except WebDriverException as err:
        print(f"WebDriver error: {err}")
    except Exception as err:
        print(f"Unexpected error: {type(err).__name__}: {err}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()