import asyncio
from monarchmoney import MonarchMoney
import gspread
from oauth2client.service_account import ServiceAccountCredentials

async def fetch_and_store_balance():
    print("Starting balance retrieval...")

    # Step 1: Log in to Monarch Money
    mm = MonarchMoney()
    await mm.login(email="baespey@gmail.com", password="gHn63sUR$S5!qxgI", mfa_secret_key="ez4wwmhv")
    print("Logged into Monarch Money.")

    # Step 2: Sync accounts and get the latest balance
    await mm.request_accounts_refresh_and_wait()
    accounts = await mm.get_accounts()
    chase_account = next(acc for acc in accounts if acc['name'] == "Chase Checking")
    latest_balance = chase_account['balance']
    print(f"Retrieved latest balance: {latest_balance}")

    # Step 3: Update the Google Sheet
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('path/to/creds.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open("Your Spreadsheet Name").sheet1
    sheet.update('A1', latest_balance)
    print("Balance updated in Google Sheet.")

if __name__ == "__main__":
    asyncio.run(fetch_and_store_balance())
    print("Script completed successfully.")
