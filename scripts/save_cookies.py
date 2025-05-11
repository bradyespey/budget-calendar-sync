# scripts/save_cookies.py

import os
import json
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException

# ── Configuration ─────────────────────────────────────────────────────────
COOKIE_PATH       = r"C:\Projects\Budget\monarch_cookies.json"
LOGIN_URL         = "https://app.monarchmoney.com/login"
CHROMEDRIVER_PATH = r"C:\Drivers\Chrome\chromedriver.exe"

# ── Ensure directory exists ────────────────────────────────────────────────
def ensure_dir_for(path: str) -> None:
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d)

# ── Create a new Chrome session (ephemeral profile) ───────────────────────
def init_driver() -> webdriver.Chrome:
    opts = webdriver.ChromeOptions()
    opts.add_argument("--start-maximized")
    opts.add_argument("--disable-logging")
    opts.add_argument("--log-level=3")
    service = Service(CHROMEDRIVER_PATH)
    return webdriver.Chrome(service=service, options=opts)

# ── Main routine ──────────────────────────────────────────────────────────
def main() -> None:
    driver = None
    try:
        driver = init_driver()
        driver.get(LOGIN_URL)
        print("Please log in to Monarch Money (including MFA) in the opened browser.")
        input("Press Enter once you log in and see your dashboard…")

        cookies = driver.get_cookies()
        ensure_dir_for(COOKIE_PATH)
        with open(COOKIE_PATH, "w", encoding="utf-8") as f:
            json.dump(cookies, f, indent=2)

        print(f"Saved {len(cookies)} cookies to {COOKIE_PATH}")

    except WebDriverException as err:
        print(f"WebDriver error: {err}")
        sys.exit(1)
    except Exception as err:
        print(f"Unexpected error: {err}")
        sys.exit(1)
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()