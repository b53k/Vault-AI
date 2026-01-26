"""
    Admin service for aggregating analytics data across all users.
    This provides dashboard-level insights.
"""

from typing import Dict, Any, List, Optional
from app.config.database import db_connection
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class AdminService:
    def get_stats(self) -> Dict[str, Any]:

        with db_connection.get_connection() as conn:
            with conn.cursor() as cur:
                # count total users
                cur.execute("SELECT COUNT(*) FROM users")
                total_users = cur.fetchone()[0]

                # count total accounts
                cur.execute("SELECT COUNT(*) FROM accounts")
                total_accounts = cur.fetchone()[0]

                # count total transactions
                cur.execute("SELECT COUNT(*) FROM transactions")
                total_transactions = cur.fetchone()[0]

                # calculate total balance
                cur.execute("SELECT SUM(balance) FROM accounts")
                total_balance = cur.fetchone()[0]
                total_balance = float(total_balance_result) if total_balance_result else 0.0

                return {
                    "total_users": total_users,
                    "total_accounts": total_accounts,
                    "total_transactions": total_transactions,
                    "total_balance": round(total_balance, 2)
                }
    

    def get_users(
        self,
        page: int = 1,
        page_size: int = 50,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a paginated list of users with optional search.

        Args:
            page: Page number (1-indexed)
            page_size: Number of users per page
            search: Optional search term for name/email
        
        Returns:
            Dictionary with users list and pagination info
        """

        offset = (page - 1) * page_size

        with db_connection.get_connection() as conn:
            with conn.cursor() as cur:
                base_query = "SELECT user_id, name, email, phone, city, state, risk_score FROM users"
                count_query = "SELECT COUNT(*) FROM users"
                params = []

                if search:
                    base_query += "WHERE name ILIKE %s OR email ILIKE %s"
                    count_query += "WHERE name ILIKE %s OR email ILIKE %s"
                    search_term = f"%{search}%"
                    params = [search_term, search_term]

                base_query += "ORDER BY user_id DESC LIMIT %s OFFSET %s"
                params.extend([page_size, offset])

                # Get total count
                cur.execute(count_query, params[:2] if search else [])
                total = cur.fetchone()[0]

                # Get users
                cur.execute(base_query, params)
                columns = [desc[0] for desc in cur.description]
                results = cur.fetchall()
                
                users = [dict(zip(columns, row)) for row in results]

                return {
                    "users": users,
                    "pagination": {
                        "page": page,
                        "page_size": page_size,
                        "total": total,
                        "total_pages": (total + page_size - 1) // page_size
                    }
                }

    
    def get_user_details(self, user_id: int) -> Dict[str, Any]:
        """
        Get detailed information about a specific user.
        
        Args:
            user_id: The user ID
        
        Returns:
            Dictionary with user details, accounts, and transaction summary
        """
        with db_connection.get_connection() as conn:
            with conn.cursor() as cur:
                # Get user info
                cur.execute(
                    "SELECT * FROM users WHERE user_id = %s",
                    (user_id,)
                )
                user_columns = [desc[0] for desc in cur.description]
                user_row = cur.fetchone()
                
                if not user_row:
                    return {"error": "User not found"}
                
                user = dict(zip(user_columns, user_row))
                
                # Get user's accounts
                cur.execute(
                    "SELECT * FROM accounts WHERE user_id = %s",
                    (user_id,)
                )
                account_columns = [desc[0] for desc in cur.description]
                accounts = [
                    dict(zip(account_columns, row))
                    for row in cur.fetchall()
                ]
                
                # Get transaction summary
                cur.execute("""
                    SELECT 
                        COUNT(*) as total_transactions,
                        SUM(ABS(amount)) as total_spending,
                        MIN(timestamp) as first_transaction,
                        MAX(timestamp) as last_transaction
                    FROM transactions t
                    INNER JOIN accounts a ON t.account_id = a.account_id
                    WHERE a.user_id = %s AND t.amount < 0
                """, (user_id,))
                
                summary_row = cur.fetchone()
                transaction_summary = {
                    "total_transactions": summary_row[0] or 0,
                    "total_spending": float(summary_row[1]) if summary_row[1] else 0.0,
                    "first_transaction": summary_row[2].isoformat() if summary_row[2] else None,
                    "last_transaction": summary_row[3].isoformat() if summary_row[3] else None
                }
                
                return {
                    "user": user,
                    "accounts": accounts,
                    "transaction_summary": transaction_summary
                }
    
    
    def get_trends(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        group_by: str = "month"
    ) -> Dict[str, Any]:
        """
        Get spending trends over time.
        
        Args:
            start_date: Start date for trends
            end_date: End date for trends
            group_by: How to group ("day", "week", "month")
        
        Returns:
            Dictionary with trend data
        """
        # Default to last 6 months
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=180)
        
        # Determine date truncation based on group_by
        truncate_map = {
            "day": "day",
            "week": "week",
            "month": "month"
        }
        truncate = truncate_map.get(group_by, "month")
        
        with db_connection.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(f"""
                    SELECT 
                        DATE_TRUNC('{truncate}', t.timestamp) as period,
                        COUNT(*) as transaction_count,
                        SUM(ABS(t.amount)) as total_spending,
                        COUNT(DISTINCT a.user_id) as unique_users
                    FROM transactions t
                    INNER JOIN accounts a ON t.account_id = a.account_id
                    WHERE t.timestamp >= %s AND t.timestamp < %s
                      AND t.amount < 0
                    GROUP BY DATE_TRUNC('{truncate}', t.timestamp)
                    ORDER BY period ASC
                """, (start_date, end_date))
                
                columns = [desc[0] for desc in cur.description]
                results = cur.fetchall()
                
                trends = []
                for row in results:
                    row_dict = dict(zip(columns, row))
                    # Convert datetime to ISO string
                    if row_dict['period']:
                        row_dict['period'] = row_dict['period'].isoformat()
                    # Convert decimal to float
                    if row_dict['total_spending']:
                        row_dict['total_spending'] = float(row_dict['total_spending'])
                    trends.append(row_dict)
                
                return {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "group_by": group_by,
                    "trends": trends
                }
    
    def get_geographic_distribution(self) -> Dict[str, Any]:
        """
        Get user distribution by state (for choropleth map).
        
        Returns:
            Dictionary with state-level user counts
        """
        with db_connection.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        state,
                        COUNT(*) as user_count,
                        AVG(risk_score) as avg_risk_score
                    FROM users
                    GROUP BY state
                    ORDER BY user_count DESC
                """)
                
                columns = [desc[0] for desc in cur.description]
                results = cur.fetchall()
                
                distribution = []
                for row in results:
                    row_dict = dict(zip(columns, row))
                    if row_dict['avg_risk_score']:
                        row_dict['avg_risk_score'] = float(row_dict['avg_risk_score'])
                    distribution.append(row_dict)
                
                return {
                    "distribution": distribution,
                    "total_states": len(distribution)
                }
    
    def get_risk_scores(self) -> Dict[str, Any]:
        """
        Get risk score distribution across all users.
        
        Returns:
            Dictionary with risk score statistics
        """
        with db_connection.get_connection() as conn:
            with conn.cursor() as cur:
                # Get risk score statistics
                cur.execute("""
                    SELECT 
                        MIN(risk_score) as min_risk,
                        MAX(risk_score) as max_risk,
                        AVG(risk_score) as avg_risk,
                        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY risk_score) as median_risk,
                        COUNT(*) FILTER (WHERE risk_score < 0.3) as low_risk_count,
                        COUNT(*) FILTER (WHERE risk_score >= 0.3 AND risk_score < 0.7) as medium_risk_count,
                        COUNT(*) FILTER (WHERE risk_score >= 0.7) as high_risk_count
                    FROM users
                """)
                
                columns = [desc[0] for desc in cur.description]
                row = cur.fetchone()
                stats = dict(zip(columns, row))
                
                # Convert to floats
                for key, value in stats.items():
                    if value is not None and isinstance(value, (int, float)):
                        stats[key] = float(value)
                
                # Get top 10 highest risk users
                cur.execute("""
                    SELECT user_id, name, email, risk_score, state
                    FROM users
                    ORDER BY risk_score DESC
                    LIMIT 10
                """)
                
                columns = [desc[0] for desc in cur.description]
                high_risk_users = [
                    dict(zip(columns, row))
                    for row in cur.fetchall()
                ]
                
                # Convert risk_score to float
                for user in high_risk_users:
                    if user['risk_score']:
                        user['risk_score'] = float(user['risk_score'])
                
                return {
                    "statistics": stats,
                    "high_risk_users": high_risk_users
                }


# Create singleton instance
admin_service = AdminService()