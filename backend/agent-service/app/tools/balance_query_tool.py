import os
import httpx
from typing import Dict, Any, Optional
from datetime import datetime

class BalanceQueryTool:
    def __init__(self):
        self.balance_url = os.getenv(
            "DATABASE_SERVICE_URL",
            "http://localhost:8002"    # Default port for database-service
        )

    async def get_balance(
        self,
        user_id: int,
        account_id: Optional[int] = None,
        account_type: Optional[str] = None,
    ) -> Dict[str, Any]:

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.balance_url}/analytics/balance/",
                json = {
                    "user_id": user_id,
                    "account_id": account_id,
                    "account_type": account_type,
                }
            )

            response.raise_for_status()
            return response.json()


# Tool instance for agent use
balance_tool = BalanceQueryTool()