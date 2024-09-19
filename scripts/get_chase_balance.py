import aiohttp
import asyncio
import json

# Function to load credentials from a JSON file
def load_credentials(filepath):
    with open(filepath, 'r') as file:
        credentials = json.load(file)
    return credentials['email'], credentials['password']

async def get_chase_balance():
    # Load credentials from the JSON file
    email, password = load_credentials("C:\\Projects\\\\BudgetCalendar\\credentials.json")

    class MonarchMoneyClient:
        BASE_URL = "https://api.monarchmoney.com"

        def __init__(self, email, password):
            self.email = email
            self.password = password
            self.token = None
            self.headers = {"Content-Type": "application/json"}

        async def login(self):
            login_data = {"username": self.email, "password": self.password}
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.BASE_URL}/auth/login/", json=login_data) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.token = result.get('token')
                        self.headers["Authorization"] = f"Token {self.token}"
                        print("Login successful!")
                    else:
                        print(f"Login failed with status {response.status}")

        async def fetch_account_data(self):
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.post(f"{self.BASE_URL}/graphql", json={
                    "operationName": "Web_GetAccountsPage",
                    "variables": {},
                    "query": '''
                        query Web_GetAccountsPage {
                            accountTypeSummaries {
                                type {
                                    display
                                }
                                accounts {
                                    id
                                    displayName
                                    displayBalance
                                }
                            }
                        }
                    '''
                }) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data['data']['accountTypeSummaries']
                    else:
                        print(f"Failed to fetch account data with status {response.status}")

        def display_joint_checking_balance(self, account_summaries):
            for summary in account_summaries:
                for account in summary['accounts']:
                    if account['displayName'] == "Joint Checking":
                        print(f"\nJoint Checking Balance: {account['displayBalance']}")
                        return account['displayBalance']
            print("\nJoint Checking account not found.")

    client = MonarchMoneyClient(email, password)
    await client.login()

    if client.token:
        account_summaries = await client.fetch_account_data()
        return client.display_joint_checking_balance(account_summaries)
    else:
        return None
