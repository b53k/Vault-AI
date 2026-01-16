import os
import httpx
from typing import Dict, Any, Optional
from datetime import datetime

class SQLAnalyticsTool:
    def __init__(self):
        self.database_service_url = os.getenv(
            "DATABASE_SERVICE_URL",
            "http://localhost:8002"    # Default port for database-service
        )

    async def analyze_spending(
        self,
        user_id: int,
        category: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        group_by: str = "category",
        account_id: Optional[int] = None,
        account_type: Optional[str] = None,
    ) -> Dict[str, Any]:

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.database_service_url}/analytics/spending/",
                json = {
                    "user_id": user_id,
                    "category": category,
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None,
                    "group_by": group_by,
                    "account_id": account_id,
                    "account_type": account_type,
                }
            )

            response.raise_for_status()
            return response.json()

# Tool instance for agent use
sql_analytics_tool = SQLAnalyticsTool()