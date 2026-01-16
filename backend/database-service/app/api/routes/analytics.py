"""
    Create a REST API router for analyzing spending data
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from app.services.spending_service import spending_service
from datetime import datetime

router = APIRouter(prefix="/analytics/spending", tags=["analytics"])

class SpendingRequest(BaseModel):
    user_id: int
    category: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    group_by: str = "category"
    account_id: Optional[int] = None
    account_type: Optional[str] = None

class SpendingResponse(BaseModel):
    user_id: int
    start_date: str
    end_date: str
    filters: Dict[str, Any]
    group_by: str
    summary: Dict[str, Any]
    results: List[Dict[str, Any]]


@router.post("/", response_model=SpendingResponse)
async def analyze_spending(request: SpendingRequest):
    """Analyze spending data for a given user"""

    try:
        results = spending_service.analyze_spending(
            user_id = request.user_id,
            category = request.category,
            start_date = request.start_date,
            end_date = request.end_date,
            group_by = request.group_by,
            account_id = request.account_id,
            account_type = request.account_type,
        )

        return SpendingResponse(**results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


