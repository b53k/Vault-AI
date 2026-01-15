"""
    Create a REST API router for searching policy documents
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import traceback
from app.vectorstore.search_service import vector_search_service

router = APIRouter(prefix="/search", tags=["vector-search"])

class SearchRequest(BaseModel):
    query: str
    similarity_threshold: Optional[float] = 0.7
    max_results: Optional[int] = 5

class SearchResponse(BaseModel):
    results: list
    query: str
    count: int

# End-point: /search/
@router.post("/", response_model=SearchResponse)
async def search_policy(request: SearchRequest):
    """Search policy documents using vector similarity"""

    try:
        results = vector_search_service.search(
            query = request.query,
            similarity_threshold = request.similarity_threshold,
            max_results = request.max_results
        )

        return SearchResponse(
            results = results,
            query = request.query,
            count = len(results)
        )
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Error in search_policy: {error_trace}")
        raise HTTPException(status_code=500, detail=f"{str(e)}\n\n{error_trace}")


# End-point: /search/rag-context
@router.post("/rag-context")
async def get_rag_context(request: SearchRequest):
    """Get formatted context for RAG"""

    try:
        context = vector_search_service.get_context_for_rag(
            query = request.query,
            max_chunks = request.max_results or 3,
            similarity_threshold = request.similarity_threshold
        )

        return {"context": context, "query": request.query}
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Error in search_policy: {error_trace}")
        raise HTTPException(status_code=500, detail=f"{str(e)}\n\n{error_trace}")