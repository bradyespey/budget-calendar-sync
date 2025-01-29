import asyncio
import os
import json
from monarchmoney import MonarchMoney, LoginFailedException, RequestFailedException

async def main():
    # Load credentials from the JSON file
    credentials_file = os.path.join(os.path.dirname(__file__), "credentials.json")
    with open(credentials_file) as f:
        credentials = json.load(f)
    
    email = credentials["email"]
    password = credentials["password"]
    
    # Initialize the MonarchMoney client
    client = MonarchMoney()
    
    # Attempt to log in
    try:
        await client.login(email=email, password=password)
        print("Login successful!")
    except LoginFailedException as e:
        print(f"Login failed: {e}")
        return

    # Fetch the account IDs, so we can pass the correct account ID for sync
    try:
        account_data = await client.get_accounts()
        print("Accounts fetched successfully.")
        
        # Find the ID for the "Joint Checking" account
        joint_checking_account_id = None
        for account in account_data["accounts"]:
            if account["displayName"] == "Joint Checking":
                joint_checking_account_id = account["id"]
                break
        
        if not joint_checking_account_id:
            print("Joint Checking account not found.")
            return
        
        # Start the sync process and wait for completion
        print("Initiating account sync...")
        timeout = 600  # Increase the timeout to 10 minutes
        delay = 30     # Check every 30 seconds
        refresh_success = await client.request_accounts_refresh_and_wait([joint_checking_account_id], timeout=timeout, delay=delay)
        
        if refresh_success:
            print("Account sync completed successfully!")
        else:
            print("Account sync did not complete within the expected time.")
            return

        # Fetch the balance again after the sync
        updated_account_data = await client.get_accounts()
        for account in updated_account_data["accounts"]:
            if account["id"] == joint_checking_account_id:
                print(f"Joint Checking Balance after sync: {account['displayBalance']}")
                break

    except RequestFailedException as e:
        print(f"Request failed: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Run the script
if __name__ == "__main__":
    asyncio.run(main())
