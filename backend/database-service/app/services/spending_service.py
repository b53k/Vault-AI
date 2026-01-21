from typing import Dict, Optional, Any
from app.config.database import db_connection
from datetime import datetime, timedelta

# Database date constraints
MAX_END_DATE = datetime(2026, 1, 13, 23, 59, 33, 593266)
MIN_START_DATE = datetime(2025, 1, 13, 23, 59, 33, 593266)  # One year before MAX_END_DATE

class SpendingService:
    def analyze_spending(
        self,
        user_id: int,
        category: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        group_by: str = "category",
        account_id: Optional[int] = None,
        account_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze spending data for a given user

        Args:
            user_id: User ID to analyze
            category: Optional category filter (e.g., "Coffee Shops", "Groceries")
            start_date: Start date for analysis (defaults to 30 days ago)
            end_date: End date for analysis (defaults to now)
            group_by: How to group results ("category", "merchant", "month", "account")
            account_id: Optional - filter by specific account_id
            account_type: Optional - filter by account type ("checking" or "savings")
        
        Returns:
            Dictionary with aggregated spending results
        """

        # Default date range: last 30 days
        if end_date is None:
            end_date = datetime.now()

        end_date = min(end_date, MAX_END_DATE)
        end_date = max(end_date, MIN_START_DATE)

        if start_date is None:
            start_date = end_date - timedelta(days=30)
        
        start_date = max(start_date, MIN_START_DATE)
        start_date = min(start_date, end_date)

        # Ensure start date is not more than one year before end date
        min_valid_start = end_date - timedelta(days=365)
        start_date = max(start_date, min_valid_start)

        #----------------------------------------------------

        # Build WHERE clause conditions
        conditions = ["a.user_id = %s"]
        params = [user_id]

        # Date filtering
        conditions.append("t.timestamp >= %s")
        params.append(start_date)
        conditions.append("t.timestamp < %s")
        params.append(end_date)

        # Account filtering
        if account_id is not None:
            conditions.append("a.account_id = %s")
            params.append(account_id)

        if account_type is not None:
            conditions.append("LOWER(a.type) = %s")
            params.append(account_type.lower())

        # Category filtering
        if category is not None:
            conditions.append("t.category = %s")
            params.append(category)

        # Only include spenddings i.e. -ve amounts
        conditions.append("t.amount < 0")

        # ----------------------------------------------------

        # Build GROUP BY clause
        group_by_map = {
            "category": "t.category",
            "merchant": "t.merchant",
            "month": "DATE_TRUNC('month', t.timestamp)",
            "account": "a.account_id, a.type"
        }

        group_by_clause = group_by_map.get(group_by, "t.category")

        # ----------------------------------------------------

        # Build SELECT clause based on group_by
        if group_by == "account":
            select_clause = """
                a.account_id,
                a.type as account_type,
                COUNT(*) as transaction_count,
                SUM(ABS(t.amount)) as total_spending
            """
        elif group_by == "month":
            select_clause = """
                DATE_TRUNC('month', t.timestamp) as month,
                COUNT(*) as transaction_count,
                SUM(ABS(t.amount)) as total_spending
            """
        else:
            select_clause = f"""
                {group_by_clause} as group_value,
                COUNT(*) as transaction_count,
                SUM(ABS(t.amount)) as total_spending
            """
        
        # Build final query
        query = f"""
            SELECT
                {select_clause}
            FROM transactions t
            INNER JOIN accounts a ON t.account_id = a.account_id
            WHERE {' AND '.join(conditions)}
            GROUP BY {group_by_clause}
            ORDER BY total_spending DESC
            LIMIT 50
        """

        # ----------------------------------------------------

        # Execute query
        with db_connection.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                columns = [desc[0] for desc in cur.description]
                results = cur.fetchall()

                rows = []
                for row in results:
                    row_dict = dict(zip(columns, row))
                    # Convert datetime objects to ISO format strings for JSON serialization
                    if 'month' in row_dict and row_dict['month'] is not None:
                        if hasattr(row_dict['month'], 'isoformat'):
                            row_dict['month'] = row_dict['month'].isoformat()
                        elif hasattr(row_dict['month'], 'strftime'):
                            row_dict['month'] = row_dict['month'].strftime('%Y-%m-%dT%H:%M:%S')
                    
                    if 'total_spending' in row_dict and row_dict['total_spending'] is not None:
                        row_dict['total_spending'] = float(row_dict['total_spending'])
                    rows.append(row_dict)
        
        total_spending = sum(row.get('total_spending', 0) for row in rows)
        total_transactions = sum(row.get('transaction_count', 0) for row in rows)

        # Format response
        return {
            "user_id": user_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "filters": {
                "account_id": account_id,
                "account_type": account_type,
                "category": category
            },
            "group_by": group_by,
            "summary": {
                "total_transactions": total_transactions,
                "total_spending": round(total_spending, 2)
            },
            "results": rows
        }

# create singleton instance
spending_service = SpendingService()