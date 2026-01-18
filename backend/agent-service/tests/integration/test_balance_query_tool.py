# backend/agent-service/tests/integration/test_balance_query_tool.py
import asyncio
import sys
from pathlib import Path

# Add parent directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.tools.balance_query_tool import BalanceQueryTool

async def test_balance_query_tool():
    """Test BalanceQueryTool functionality"""
    tool = BalanceQueryTool()
    
    # Use a test user_id (adjust based on your data)
    test_user_id = 11  # Based on your terminal output
    
    print(f"Testing Balance Query Tool for user_id: {test_user_id}\n")
    
    # Test 1: Get all accounts for user
    print("=" * 50)
    print("Test 1: get_balance() - All accounts")
    print("=" * 50)
    try:
        results = await tool.get_balance(user_id=test_user_id)
        print(f"✓ Success!")
        print(f"User ID: {results.get('user_id')}")
        print(f"Filters: {results.get('filters')}")
        print(f"Number of accounts: {len(results.get('results', []))}")
        
        if results.get('results'):
            print(f"\nAccount details:")
            total_balance = 0
            for i, account in enumerate(results['results'], 1):
                account_id = account.get('account_id', 'N/A')
                account_type = account.get('type', 'N/A')
                balance = float(account.get('balance', 0))
                total_balance += balance
                print(f"  {i}. Account {account_id} ({account_type}): ${balance:,.2f}")
            print(f"\nTotal balance across all accounts: ${total_balance:,.2f}")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n")
    
    # Test 2: Get balance for specific account_id
    print("=" * 50)
    print("Test 2: get_balance() - Filter by account_id")
    print("=" * 50)
    try:
        test_account_id = 23  # Based on your terminal output
        
        results = await tool.get_balance(
            user_id=test_user_id,
            account_id=test_account_id
        )
        print(f"✓ Success!")
        print(f"User ID: {results.get('user_id')}")
        print(f"Account ID filter: {test_account_id}")
        print(f"Number of accounts: {len(results.get('results', []))}")
        
        if results.get('results'):
            account = results['results'][0]
            account_id = account.get('account_id', 'N/A')
            account_type = account.get('type', 'N/A')
            balance = float(account.get('balance', 0))
            print(f"\nAccount details:")
            print(f"  Account ID: {account_id}")
            print(f"  Type: {account_type}")
            print(f"  Balance: ${balance:,.2f}")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n")
    
    # Test 3: Get balance for specific account_type
    print("=" * 50)
    print("Test 3: get_balance() - Filter by account_type (savings)")
    print("=" * 50)
    try:
        results = await tool.get_balance(
            user_id=test_user_id,
            account_type="savings"
        )
        print(f"✓ Success!")
        print(f"User ID: {results.get('user_id')}")
        print(f"Account type filter: savings")
        print(f"Number of accounts: {len(results.get('results', []))}")
        
        if results.get('results'):
            print(f"\nSavings accounts:")
            total_savings = 0
            for i, account in enumerate(results['results'], 1):
                account_id = account.get('account_id', 'N/A')
                balance = float(account.get('balance', 0))
                total_savings += balance
                print(f"  {i}. Account {account_id}: ${balance:,.2f}")
            print(f"\nTotal savings balance: ${total_savings:,.2f}")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n")
    
    # Test 4: Get balance for checking accounts
    print("=" * 50)
    print("Test 4: get_balance() - Filter by account_type (checking)")
    print("=" * 50)
    try:
        results = await tool.get_balance(
            user_id=test_user_id,
            account_type="checking"
        )
        print(f"✓ Success!")
        print(f"User ID: {results.get('user_id')}")
        print(f"Account type filter: checking")
        print(f"Number of accounts: {len(results.get('results', []))}")
        
        if results.get('results'):
            print(f"\nChecking accounts:")
            total_checking = 0
            for i, account in enumerate(results['results'], 1):
                account_id = account.get('account_id', 'N/A')
                balance = float(account.get('balance', 0))
                total_checking += balance
                print(f"  {i}. Account {account_id}: ${balance:,.2f}")
            print(f"\nTotal checking balance: ${total_checking:,.2f}")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n")
    
    # Test 5: Get balance with both account_id and account_type (should match)
    print("=" * 50)
    print("Test 5: get_balance() - Filter by account_id AND account_type")
    print("=" * 50)
    try:
        test_account_id = 23
        test_account_type = "savings"
        
        results = await tool.get_balance(
            user_id=test_user_id,
            account_id=test_account_id,
            account_type=test_account_type
        )
        print(f"✓ Success!")
        print(f"User ID: {results.get('user_id')}")
        print(f"Account ID filter: {test_account_id}")
        print(f"Account type filter: {test_account_type}")
        print(f"Number of accounts: {len(results.get('results', []))}")
        
        if results.get('results'):
            account = results['results'][0]
            account_id = account.get('account_id', 'N/A')
            account_type = account.get('type', 'N/A')
            balance = float(account.get('balance', 0))
            print(f"\nAccount details:")
            print(f"  Account ID: {account_id}")
            print(f"  Type: {account_type}")
            print(f"  Balance: ${balance:,.2f}")
            
            # Verify filters match
            if account_id == test_account_id and account_type == test_account_type:
                print(f"\n✓ Filters match account details!")
            else:
                print(f"\n✗ Warning: Filters don't match account details")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n")
    
    # Test 6: Test with invalid account_id (should return empty)
    print("=" * 50)
    print("Test 6: get_balance() - Invalid account_id (should return empty)")
    print("=" * 50)
    try:
        invalid_account_id = 99999
        
        results = await tool.get_balance(
            user_id=test_user_id,
            account_id=invalid_account_id
        )
        print(f"✓ Success!")
        print(f"User ID: {results.get('user_id')}")
        print(f"Account ID filter: {invalid_account_id}")
        print(f"Number of accounts: {len(results.get('results', []))}")
        
        if len(results.get('results', [])) == 0:
            print(f"\n✓ Correctly returned empty results for invalid account_id")
        else:
            print(f"\n✗ Warning: Expected empty results but got {len(results.get('results', []))} accounts")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n")
    print("=" * 50)
    print("All tests completed!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_balance_query_tool())