# scripts/save_profile.py

import os, sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

PROFILE_DIR       = r"C:\Projects\Budget\chrome_profile"
CHROMEDRIVER_EXE  = r"C:\Drivers\Chrome\chromedriver.exe"
LOGIN_URL         = "https://app.monarchmoney.com/login"

os.makedirs(PROFILE_DIR, exist_ok=True)

opts = webdriver.ChromeOptions()
opts.add_argument(f"--user-data-dir={PROFILE_DIR}")      # ← persistent profile
opts.add_argument("--start-maximized")
driver = webdriver.Chrome(service=Service(CHROMEDRIVER_EXE), options=opts)

print("Log in to Monarch (incl. MFA) then press <Enter> here …")
driver.get(LOGIN_URL)
input()
driver.quit()
print("Profile saved in", PROFILE_DIR)