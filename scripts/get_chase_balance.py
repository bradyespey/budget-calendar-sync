# scripts/get_chase_balance.py

import aiohttp
import asyncio
import json
import os

# Specify project path folders and set variables
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, os.pardir))
TOKEN_PATH = os.path.join(PROJECT_ROOT, "monarch_token.json")

def load_token(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Token file not found: {filepath}")
    with open(filepath, "r") as f:
        data = json.load(f)
    return data.get("token")

async def get_chase_balance_async():
    token = load_token(TOKEN_PATH)
    if not token:
        raise ValueError("No token found. Please run the authentication script first.")

    headers = {
        "Content-Type": "application/json",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/116.0.5845.140 Safari/537.36"
        ),
        "Origin": "https://app.monarchmoney.com",
        "Referer": "https://app.monarchmoney.com",
        # Use "Token" instead of "Bearer"
        "Authorization": f"Token {token}"
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        graphql_url = "https://api.monarchmoney.com/graphql"
        payload = {
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
        }

        async with session.post(graphql_url, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                for summary in data['data']['accountTypeSummaries']:
                    for account in summary['accounts']:
                        if account['displayName'] == "Joint Checking":
                            print("Joint Checking Balance:", account['displayBalance'])
                            return account['displayBalance']
                raise ValueError("Joint Checking account not found.")
            else:
                text = await response.text()
                raise ValueError(f"Failed to fetch account data: {response.status} {text}")

def get_joint_checking_balance():
    """Synchronous wrapper to fetch the Joint Checking balance."""
    return asyncio.run(get_chase_balance_async())

if __name__ == "__main__":
    try:
        balance = get_joint_checking_balance()
        print("Final Balance:", balance)
    except Exception as e:
        print("Error:", e)