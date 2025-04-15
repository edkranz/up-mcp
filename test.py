import asyncio
from datetime import datetime, timedelta
import up_mcp

async def main():
    print(await up_mcp.get_user_id())
    accounts = await up_mcp.get_accounts()
    print(accounts)
    print(await up_mcp.get_account(accounts[0].get("id")))
    
    # categories = await up_mcp.get_categories()
    # print(categories)
    
    # Get transactions
    transactions = await up_mcp.get_transactions(
        since=datetime.now() - timedelta(days=7),
        category_id=None
    )
    print("Recent transactions:", transactions)
    

if __name__ == "__main__":
    asyncio.run(main())