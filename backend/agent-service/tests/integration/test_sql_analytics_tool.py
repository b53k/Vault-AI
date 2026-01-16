# backend/agent-service/tests/integration/test_sql_analytics_tool.py
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.tools.sql_analytics_tool import SQLAnalyticsTool

async def test_sql_analytics_tool():
    """Test SQLAnalyticsTool functionality"""
    tool = SQLAnalyticsTool()
    
    # Use a test user_id (adjust based on your data)
    test_user_id = 8
    
    print(f"Testing SQL Analytics Tool for user_id: {test_user_id}\n")
    
    # Test 1: Basic spending analysis (all accounts, default date range)
    print("=" * 50)
    print("Test 1: analyze_spending() - Basic (all accounts, last 30 days)")
    print("=" * 50)
    try:
        results = await tool.analyze_spending(user_id=test_user_id)
        print(f"✓ Success!")
        print(f"Summary:")
        print(f"  Total transactions: {results.get('summary', {}).get('total_transactions', 0)}")
        print(f"  Total spending: ${results.get('summary', {}).get('total_spending', 0):.2f}")
        print(f"  Results count: {len(results.get('results', []))}")
        if results.get('results'):
            print(f"\nTop 3 categories:")
            for i, item in enumerate(results['results'][:3], 1):
                group_value = item.get('group_value', 'N/A')
                spending = float(item.get('total_spending', 0))
                count = int(item.get('transaction_count', 0))
                print(f"  {i}. {group_value}: ${spending:.2f} ({count} transactions)")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n")
    
    # Test 2: Spending by category with date range
    print("=" * 50)
    print("Test 2: analyze_spending() - With date range (last 7 days)")
    print("=" * 50)
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        results = await tool.analyze_spending(
            user_id=test_user_id,
            start_date=start_date,
            end_date=end_date,
            group_by="category"
        )
        print(f"✓ Success!")
        print(f"Date range: {start_date.date()} to {end_date.date()}")
        print(f"Total spending: ${results.get('summary', {}).get('total_spending', 0):.2f}")
        print(f"Results: {len(results.get('results', []))} categories")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n")
    
    # Test 3: Filter by category
    print("=" * 50)
    category = "Entertainment"
    print(f"Test 3: analyze_spending() - Filter by category ({category})")
    print("=" * 50)
    try:
        results = await tool.analyze_spending(
            user_id=test_user_id,
            category=category,
            group_by="merchant"
        )
        print(f"✓ Success!")
        print(f"Category filter: {category}")
        print(f"Total spending: ${results.get('summary', {}).get('total_spending', 0):.2f}")
        if results.get('results'):
            print(f"\nTop merchants:")
            for item in results['results'][:5]:
                merchant = item.get('group_value', 'N/A')
                spending = float(item.get('total_spending', 0))
                print(f"  - {merchant}: ${spending:.2f}")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n")
    
    # Test 4: Filter by account type
    print("=" * 50)
    print("Test 4: analyze_spending() - Filter by account type (checking)")
    print("=" * 50)
    try:
        results = await tool.analyze_spending(
            user_id=test_user_id,
            account_type="checking",
            group_by="category"
        )
        print(f"✓ Success!")
        print(f"Account type filter: checking")
        print(f"Total spending: ${results.get('summary', {}).get('total_spending', 0):.2f}")
        print(f"Results: {len(results.get('results', []))} categories")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n")
    
    # Test 5: Group by month
    print("=" * 50)
    print("Test 5: analyze_spending() - Group by month (last 6 months)")
    print("=" * 50)
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)  # 6 months
        
        results = await tool.analyze_spending(
            user_id=test_user_id,
            start_date=start_date,
            end_date=end_date,
            group_by="month"
        )
        print(f"✓ Success!")
        print(f"Date range: {start_date.date()} to {end_date.date()}")
        print(f"Total spending: ${results.get('summary', {}).get('total_spending', 0):.2f}")
        if results.get('results'):
            print(f"\nMonthly breakdown:")
            for item in results['results']:
                month = item.get('month', 'N/A')
                spending = float(item.get('total_spending', 0))
                count = int(item.get('transaction_count', 0))
                # Format month - should be ISO string from service, but handle other formats
                if isinstance(month, str):
                    # If it's an ISO string, extract just YYYY-MM
                    if 'T' in month:
                        month_str = month.split('T')[0][:7]  # Get YYYY-MM from YYYY-MM-DDTHH:MM:SS
                    else:
                        month_str = month[:7] if len(month) >= 7 else month
                elif hasattr(month, 'strftime'):
                    # It's a datetime object (fallback)
                    month_str = month.strftime('%Y-%m')
                else:
                    month_str = str(month)
                print(f"  - {month_str}: ${spending:.2f} ({count} transactions)")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n")
    
    # Test 6: Group by account
    print("=" * 50)
    print("Test 6: analyze_spending() - Group by account")
    print("=" * 50)
    try:
        results = await tool.analyze_spending(
            user_id=test_user_id,
            group_by="account"
        )
        print(f"✓ Success!")
        print(f"Total spending: ${results.get('summary', {}).get('total_spending', 0):.2f}")
        if results.get('results'):
            print(f"\nAccount breakdown:")
            for item in results['results']:
                account_id = item.get('account_id', 'N/A')
                account_type = item.get('account_type', 'N/A')
                spending = float(item.get('total_spending', 0))
                count = int(item.get('transaction_count', 0))
                print(f"  - Account {account_id} ({account_type}): ${spending:.2f} ({count} transactions)")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n")
    
    # Test 7: Filter by specific account_id
    print("=" * 50)
    print("Test 7: analyze_spending() - Filter by account_id")
    print("=" * 50)
    try:
        # First, get accounts to find a valid account_id
        # For this test, we'll use account_id=1 (adjust if needed)
        test_account_id = 14
        
        results = await tool.analyze_spending(
            user_id=test_user_id,
            account_id=test_account_id,
            group_by="category"
        )
        print(f"✓ Success!")
        print(f"Account ID filter: {test_account_id}")
        print(f"Total spending: ${results.get('summary', {}).get('total_spending', 0):.2f}")
        print(f"Results: {len(results.get('results', []))} categories")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n")
    print("=" * 50)
    print("All tests completed!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_sql_analytics_tool())