"""
Admin API routes for dashboard analytics.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from app.services.admin_service import admin_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
async def get_stats():
    """
    Get overall platform statistics.
    
    Returns:
        Total users, accounts, transactions, and balance
    """
    try:
        return admin_service.get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users")
async def get_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None
):
    """
    Get paginated list of users.
    
    Args:
        page: Page number (default: 1)
        page_size: Items per page (default: 50, max: 100)
        search: Optional search term
    """
    try:
        return admin_service.get_users(page=page, page_size=page_size, search=search)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/details")
async def get_user_details(user_id: int):
    """
    Get detailed information about a specific user.
    
    Args:
        user_id: The user ID
    """
    try:
        result = admin_service.get_user_details(user_id)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends")
async def get_trends(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    group_by: str = Query("month", regex="^(day|week|month)$")
):
    """
    Get spending trends over time.
    
    Args:
        start_date: Start date (ISO format)
        end_date: End date (ISO format)
        group_by: Group by day, week, or month
    """
    try:
        return admin_service.get_trends(
            start_date=start_date,
            end_date=end_date,
            group_by=group_by
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/geographic")
async def get_geographic_distribution():
    """
    Get user distribution by state (for choropleth map).
    """
    try:
        return admin_service.get_geographic_distribution()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risk-scores")
async def get_risk_scores():
    """
    Get risk score statistics and high-risk users.
    """
    try:
        return admin_service.get_risk_scores()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))