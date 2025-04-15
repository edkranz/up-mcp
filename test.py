import pytest
import asyncio
from datetime import datetime, timedelta
import os
from typing import AsyncGenerator

import up_mcp
from upbankapi import AsyncClient, NotAuthorizedException

# Fixture to ensure UP_TOKEN is set
@pytest.fixture(scope="session", autouse=True)
def check_token():
    token = os.getenv("UP_TOKEN")
    if not token:
        pytest.skip("UP_TOKEN environment variable not set")
    return token

# Fixture for async tests
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def client(check_token) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(token=check_token) as client:
        yield client

@pytest.mark.asyncio
async def test_get_user_id():
    """Test that we can authenticate and get a user ID."""
    result = await up_mcp.get_user_id()
    assert result is not None
    assert isinstance(result, str)
    
    # Extract the actual user ID from the result
    # The format is "Authorized: {user_id}"
    assert result.startswith("Authorized: ")
    user_id = result.split("Authorized: ")[1]
    
    # Check that the user_id is a valid UUID format
    assert isinstance(user_id, str)
    # Optional: validate UUID format if needed
    import uuid
    try:
        uuid_obj = uuid.UUID(user_id)
        assert str(uuid_obj) == user_id  # Ensures it's a valid UUID string
    except ValueError:
        pytest.fail(f"User ID '{user_id}' is not a valid UUID")


@pytest.mark.asyncio
async def test_get_accounts():
    """Test retrieving all accounts."""
    accounts = await up_mcp.get_accounts()
    assert accounts is not None
    assert isinstance(accounts, list)
    assert len(accounts) > 0
    
    # Check account structure based on actual response
    account = accounts[0]
    assert "id" in account
    assert "name" in account
    assert "balance" in account
    assert isinstance(account["id"], str)
    assert isinstance(account["name"], str)
    assert isinstance(account["balance"], (int, float))


@pytest.mark.asyncio
async def test_get_specific_account():
    """Test retrieving a specific account by ID."""
    # First get all accounts
    accounts = await up_mcp.get_accounts()
    account_id = accounts[0]["id"]
    
    # Then get specific account
    account = await up_mcp.get_account(account_id)
    assert account is not None
    
    # Check the structure of the response
    # The actual response is formatted like: <Account 'Spending' (TRANSACTIONAL): 9.29 AUD>
    assert isinstance(account, str)
    assert account.startswith("<Account ")
    assert account.endswith(">")
    
    # Check that the account name from the first response is in the specific account response
    account_name = accounts[0]["name"]
    assert account_name in account


@pytest.mark.asyncio
async def test_get_transactions():
    """Test retrieving transactions with various filters."""
    # Test with date filter
    since_date = datetime.now() - timedelta(days=7)
    transactions = await up_mcp.get_transactions(since=since_date)
    assert transactions is not None
    assert isinstance(transactions, list)
    
    if len(transactions) > 0:
        # Check transaction structure based on actual response
        transaction = transactions[0]
        assert isinstance(transaction, dict)
        assert "description" in transaction
        assert "amount" in transaction
        assert isinstance(transaction["description"], str)
        assert isinstance(transaction["amount"], (int, float))
        
        # Test with verbose parameter
        verbose_transactions = await up_mcp.get_transactions(since=since_date, verbose=True)
        if len(verbose_transactions) > 0:
            verbose_tx = verbose_transactions[0]
            assert "id" in verbose_tx
            assert "status" in verbose_tx
            assert "created_at" in verbose_tx


@pytest.mark.asyncio
async def test_get_categories():
    """Test retrieving categories."""
    categories = await up_mcp.get_categories()
    assert categories is not None
    assert isinstance(categories, list)
    
    if len(categories) > 0:
        # Check category structure based on actual response
        category = categories[0]
        assert "id" in category
        assert "name" in category
        assert isinstance(category["id"], str)
        assert isinstance(category["name"], str)


@pytest.mark.asyncio
async def test_invalid_account_id():
    """Test error handling for invalid account ID."""
    with pytest.raises(Exception):  # Replace with specific exception when implemented
        await up_mcp.get_account("invalid-account-id")


@pytest.mark.asyncio
async def test_get_transaction():
    """Test retrieving a specific transaction."""
    # First get all transactions with verbose to get IDs
    transactions = await up_mcp.get_transactions(verbose=True)
    if len(transactions) > 0:
        transaction_id = transactions[0]["id"]
        
        # Get the specific transaction
        transaction = await up_mcp.get_transaction(transaction_id)
        assert transaction is not None
        
        # Check that the response is formatted properly
        # Actual response format is like: <Transaction HELD: -34.0 AUD [Claude Ai]>
        assert isinstance(transaction, str)
        assert transaction.startswith("<Transaction ")
        assert transaction.endswith(">")
        
        # Verify the transaction amount and description are present in the response
        tx_amount = str(abs(transactions[0]["amount"]))
        tx_desc = transactions[0]["description"]
        
        # The specific format might vary, but amount and description should be in the string
        assert tx_amount in transaction
        assert tx_desc in transaction


@pytest.mark.asyncio
async def test_categorize_transaction():
    """Test categorizing a transaction."""
    # First get all transactions with verbose to get IDs
    transactions = await up_mcp.get_transactions(verbose=True)
    if len(transactions) > 0:
        # Get categories to find a valid category ID
        categories = await up_mcp.get_categories()
        if len(categories) > 0:
            transaction_id = transactions[0]["id"]
            category_id = categories[0]["id"]
            
            # Attempt to categorize a transaction
            result = await up_mcp.categorize_transaction(
                transaction_id=transaction_id,
                category_id=category_id
            )
            # Verify the result
            assert result is not None
            assert isinstance(result, bool)
            assert result == True


@pytest.mark.asyncio
async def test_webhooks():
    """Test webhook operations."""
    # Get existing webhooks
    webhooks = await up_mcp.get_webhooks()
    
    # Should at least return an empty list without error
    assert isinstance(webhooks, list)
    
    # Test creating a webhook
    test_url = "https://hello.requestcatcher.com/test"
    result = await up_mcp.create_webhook(url=test_url)
    
    # Verify webhook creation result
    assert result is not None
    assert isinstance(result, dict)
    assert "id" in result
    webhook_id = result["id"]
    
    # Test pinging the webhook
    ping_result = await up_mcp.ping_webhook(webhook_id=webhook_id)
    assert ping_result is not None
    
    # Test deleting the webhook
    delete_result = await up_mcp.delete_webhook(webhook_id=webhook_id)
    assert delete_result is not None
    
    # Verify webhook was deleted by checking the list again
    updated_webhooks = await up_mcp.get_webhooks()
    assert all(webhook["id"] != webhook_id for webhook in updated_webhooks)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])