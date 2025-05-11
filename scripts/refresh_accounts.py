#!/usr/bin/env python3
# scripts/refresh_accounts.py
# ───────────────────────────────────────────────────────────────────────────
# Uses the **persistent Chrome profile** in chrome_profile to refresh all
# Monarch Money accounts. Headless when called by API/GAS, GUI when run
# manually for easy debugging. No standalone cookies file required.
# ───────────────────────────────────────────────────────────────────────────

import os, sys, time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support         import expected_conditions as EC
from selenium.webdriver.common.by        import By

# ── Config ────────────────────────────────────────────────────────────────
USE_HEADLESS      = True                  # auto-overridden below for CLI
if __name__ == "__main__":                # run manually → show browser
    USE_HEADLESS = False

PROFILE_PATH      = r"C:\Projects\Budget\chrome_profile"
CHROMEDRIVER_EXE  = r"C:\Drivers\Chrome\chromedriver.exe"
DASHBOARD_URL     = "https://app.monarchmoney.com/dashboard"
ACCOUNTS_URL      = "https://app.monarchmoney.com/accounts"

# ── Helpers ───────────────────────────────────────────────────────────────
def ensure_profile_dir() -> None:
    """Create profile dir & remove stale SingletonLock."""
    os.makedirs(PROFILE_PATH, exist_ok=True)
    lock = os.path.join(PROFILE_PATH, "SingletonLock")
    if os.path.exists(lock):
        try: os.remove(lock)
        except OSError: pass

# ── Core routine ─────────────────────────────────────────────────────────
def refresh_accounts() -> bool:
    """Return True on success, False on any failure."""
    ensure_profile_dir()

    opts = webdriver.ChromeOptions()
    opts.add_argument(f"--user-data-dir={PROFILE_PATH}")
    if USE_HEADLESS:
        opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--start-maximized")
    opts.add_experimental_option("excludeSwitches", ["enable-logging"])

    try:
        drv = webdriver.Chrome(service=Service(CHROMEDRIVER_EXE), options=opts)
    except Exception as e:
        print("ChromeDriver error:", e)
        return False

    try:
        # 1) verify login using the stored profile session
        drv.get(DASHBOARD_URL)
        WebDriverWait(drv, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[@href='/accounts']"))
        )

        # 2) trigger “Refresh all”
        drv.get(ACCOUNTS_URL)
        WebDriverWait(drv, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//span[text()='Refresh all']"))
        ).click()
        print("Refresh-all button clicked")

        # 3) optional wait / prompt in GUI mode
        if USE_HEADLESS:
            time.sleep(2)
        else:
            input("✓ Done — press <Enter> to close Chrome")

        return True

    except Exception as e:
        print("Refresh failed:", e)
        return False
    finally:
        drv.quit()

# ── CLI entry-point ───────────────────────────────────────────────────────
if __name__ == "__main__":
    sys.exit(0 if refresh_accounts() else 1)