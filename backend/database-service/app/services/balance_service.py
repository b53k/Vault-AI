from typing import Dict, Optional, Any
from app.config.database import db_connection

class BalanceService:
    def get_balance(
        self,
        user_id: int,
        account_id: Optional[int] = None,
        account_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get the balance for a given user and account
        
        Args:
            user_id: The ID of the user
            account_id: The ID of the account
            account_type: The type of the account
        
        Returns:
            A dictionary containing the balance
        """

        account_type = account_type.lower() if account_type else None

        # Build WHERE clause
        conditions = ["user_id = %s"]
        params = [user_id]

        if account_id:
            conditions.append("account_id = %s")
            params.append(account_id)
        
        if account_type:
            conditions.append("type = %s")
            params.append(account_type)
        
        where_clause = ' AND '.join(conditions)

        # Build query
        query = f"""
            SELECT * 
            FROM accounts
            WHERE {where_clause}
        """

        #Execute query
        with db_connection.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                columns = [desc[0] for desc in cur.description]
                results = cur.fetchall()

                rows = []
                for row in results:
                    row_dict = dict(zip(columns, row))
                    rows.append(row_dict)

        return {
            "user_id": user_id,
            "filters": {
                "account_id": account_id,
                "account_type": account_type,
            },
            "results": rows
        }


balance_service = BalanceService()

if __name__ == "__main__":
    balance_service = BalanceService()
    print ("="*50)
    print(balance_service.get_balance(user_id = 11, account_id = None, account_type = None))
    print ("="*50)
    print(balance_service.get_balance(user_id = 11, account_id = 23, account_type = None))
    print ("="*50)
    print(balance_service.get_balance(user_id = 11, account_id = None, account_type = "savings"))
    print ("="*50)