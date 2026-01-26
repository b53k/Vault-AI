"""
    Chat API endpoint for the agent service.
    Expose the orchestrator as a web API that can stream responses.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from app.tools.orchestrator import orchestrator

router = APIRouter(prefix = "/chat", tags = ["chat"])

class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    query: str
    user_id: int
    thread_id: Optional[str] = None     # Optional thread for conversation history


@router.post("/stream")
async def stream_chat(request: ChatRequest):
    """
    Stream chat response using Server-Sent Events (SSE) 
    -> Uni-directional data flow from server to client.

    Returns:
        StreamingResponse: SSE stream of JSON events.
    """

    try:
        async def event_generator():
            try:
                async for event in orchestrator.process_query(
                    query = request.query,
                    user_id = request.user_id,
                    thread_id = request.thread_id
                ):

                    event_json = json.dumps(event)
                    yield f"data: {event_json}\n\n"   # SSE format: data: <event_json>\n\n

                # send a final event to signal completion
                yield f"data: {json.dumps({'type': 'done'})}\n\n"

            except Exception as e:
                error_event = {
                    "type": "error",
                    "content": str(e)
                }

                yield f"data: {json.dumps(error_event)}\n\n"
    
        return StreamingResponse(
            event_generator(),
            media_type = "text/event-stream",
            headers = {
                "Cache-Control": "no-cache",    # Prevent browser caching
                "Connection": "keep-alive",     # Keep the connection open for streaming
                "X-Accel-Buffering": "no"       # Disable nginx buffering for streaming
            }
        )
    
    except Exception as e:
        # Raise error is we can't even start the streaming
        raise HTTPException(status_code = 500, detail = str(e))

