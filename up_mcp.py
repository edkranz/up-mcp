from upbankapi import AsyncClient, NotAuthorizedException
from typing import Any, Optional, Union
from datetime import datetime, timedelta
from mcp.server.fastmcp import FastMCP
import os
# Initialize FastMCP server
mcp = FastMCP("up-mcp")


UP_TOKEN = os.getenv("UP_TOKEN")

@mcp.tool()
async def get_user_id() -> str:
    """Get the user ID for the UP API.
    """

    async with AsyncClient(token=UP_TOKEN) as client:
        try:
            user_id = await client.ping()
            return f"Authorized: {user_id}"
        except NotAuthorizedException:
            return "The token is invalid"

@mcp.tool()
async def get_accounts() -> list[dict[str, Any]]:
    """Get all accounts for the user.
    """
    async with AsyncClient(token=UP_TOKEN) as client:
        accounts = await client.accounts()
        account_list = []
        async for account in accounts:
            account_list.append({
                "id": account.id,
                "name": account.name,
                "balance": account.balance
            })
        return account_list

@mcp.tool()
async def get_account(id: str) -> str:
    """Get an account for the user.

    Args:
        id: The ID of the account to get.
    """
    async with AsyncClient(token=UP_TOKEN) as client:
        account = await client.account(id)
        return str(account)

@mcp.tool()
async def get_categories(parent_id: Optional[str] = None) -> list[dict[str, Any]]:
    """Get all categories or categories under a specific parent.
    
    Args:
        parent_id: Optional ID of the parent category to filter by.
    """
    async with AsyncClient(token=UP_TOKEN) as client:
        categories = await client.categories(parent=parent_id)
        return [{"id": cat.id, "name": cat.name} for cat in categories]

@mcp.tool()
async def get_category(category_id: str) -> str:
    """Get a specific category by ID.
    
    Args:
        category_id: The ID of the category to get.
    """
    async with AsyncClient(token=UP_TOKEN) as client:
        category = await client.category(category_id)
        return str(category)

@mcp.tool()
async def categorize_transaction(transaction_id: str, category_id: Optional[str]) -> bool:
    """Categorize a transaction.
    
    Args:
        transaction_id: The ID of the transaction to categorize.
        category_id: The category ID to assign, or None to remove categorization.
    """
    async with AsyncClient(token=UP_TOKEN) as client:
        return await client.categorize(transaction_id, category_id)

@mcp.tool()
async def get_tags() -> list[dict[str, Any]]:
    """Get all tags for the user."""
    async with AsyncClient(token=UP_TOKEN) as client:
        tags = await client.tags()
        tag_list = []
        async for tag in tags:
            tag_list.append({"id": tag.id, "name": tag.name})
        return tag_list

@mcp.tool()
async def add_transaction_tags(transaction_id: str, tags: list[str]) -> bool:
    """Add tags to a transaction.
    
    Args:
        transaction_id: The ID of the transaction.
        tags: List of tag IDs to add.
    """
    async with AsyncClient(token=UP_TOKEN) as client:
        return await client.add_tags(transaction_id, *tags)

@mcp.tool()
async def remove_transaction_tags(transaction_id: str, tags: list[str]) -> bool:
    """Remove tags from a transaction.
    
    Args:
        transaction_id: The ID of the transaction.
        tags: List of tag IDs to remove.
    """
    async with AsyncClient(token=UP_TOKEN) as client:
        return await client.remove_tags(transaction_id, *tags)

@mcp.tool()
async def get_transaction(transaction_id: str) -> str:
    """Get a specific transaction by ID.
    
    Args:
        transaction_id: The ID of the transaction to get.
    """
    async with AsyncClient(token=UP_TOKEN) as client:
        transaction = await client.transaction(transaction_id)
        return str(transaction)

@mcp.tool()
async def get_transactions(
    account_id: Optional[str] = None,
    status: Optional[str] = None,
    since: Optional[datetime] = datetime.now() - timedelta(days=7),
    until: Optional[datetime] = None,
    category_id: Optional[str] = None,
    tag_id: Optional[str] = None,
    verbose: bool = False
) -> list[dict[str, Any]]:
    """Get transactions with optional filters.
    
    Args:
        account_id: Optional account ID to filter by.
        status: Optional transaction status to filter by.
        since: Optional start datetime (defaults to 7 days ago - longer may take longer to load)
        until: Optional end datetime.
        category_id: Optional category ID to filter by.
        tag_id: Optional tag ID to filter by.
    """
    async with AsyncClient(token=UP_TOKEN) as client:
        transactions = await client.transactions(
            account=account_id,
            status=status,
            since=since,
            until=until,
            category=category_id,
            tag=tag_id
        )
        transaction_list = []
        if verbose:
            async for tx in transactions:
                transaction_list.append({
                    "id": tx.id,
                    "description": tx.description,
                    "amount": tx.amount,
                    "status": tx.status,
                    "created_at": tx.created_at
                })
        else:
            async for tx in transactions:
                transaction_list.append({
                    "description": tx.description,
                    "amount": tx.amount,
                })
        return transaction_list

@mcp.tool()
async def get_webhooks() -> list[dict[str, Any]]:
    """Get all webhooks for the user."""
    async with AsyncClient(token=UP_TOKEN) as client:
        webhooks = await client.webhooks()
        webhook_list = []
        async for webhook in webhooks:
            webhook_list.append({
                "id": webhook.id,
                "url": webhook.url,
                "description": webhook.description
            })
        return webhook_list

@mcp.tool()
async def create_webhook(url: str, description: Optional[str] = None) -> dict[str, Any]:
    """Create a new webhook.
    
    Args:
        url: The URL that this webhook should post events to.
    """
    async with AsyncClient(token=UP_TOKEN) as client:
        webhook = await client.webhook.create(url, description)
        return {
            "id": webhook.id,
            "url": webhook.url,
            "description": webhook.description,
            "secret_key": webhook.secret_key,
            "created_at": webhook.created_at
        }

@mcp.tool()
async def delete_webhook(webhook_id: str) -> bool:
    """Delete a webhook.
    
    Args:
        webhook_id: The ID of the webhook to delete.
    """
    async with AsyncClient(token=UP_TOKEN) as client:
        return await client.webhook.delete(webhook_id)

@mcp.tool()
async def ping_webhook(webhook_id: str) -> str:
    """Ping a webhook.
    
    Args:
        webhook_id: The ID of the webhook to ping.
    """
    async with AsyncClient(token=UP_TOKEN) as client:
        event = await client.webhook.ping(webhook_id)
        return str(event)

if __name__ == "__main__":
    mcp.run(transport='stdio')
