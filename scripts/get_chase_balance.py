# scripts/get_chase_balance.py

import aiohttp
import asyncio
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

def load_credentials():
    email = os.getenv("MONARCH_EMAIL")
    password = os.getenv("MONARCH_PASSWORD")
    if not email or not password:
        logging.error("Environment variables MONARCH_EMAIL and MONARCH_PASSWORD must be set.")
        raise ValueError("Environment variables MONARCH_EMAIL and MONARCH_PASSWORD must be set.")
    return email, password

async def get_chase_balance():
    email, password = load_credentials()

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
                        logging.info("Login successful!")
                    else:
                        logging.error(f"Login failed with status {response.status}")
                        self.token = None

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
                        logging.error(f"Failed to fetch account data with status {response.status}")
                        return None

        def get_joint_checking_balance(self, account_summaries):
            for summary in account_summaries:
                for account in summary['accounts']:
                    if account['displayName'] == "Joint Checking":
                        logging.info(f"Joint Checking Balance: {account['displayBalance']}")
                        return account['displayBalance']
            logging.error("Joint Checking account not found.")
            return None

    client = MonarchMoneyClient(email, password)
    await client.login()

    if client.token:
        account_summaries = await client.fetch_account_data()
        if account_summaries:
            return client.get_joint_checking_balance(account_summaries)
        else:
            return None
    else:
        return None