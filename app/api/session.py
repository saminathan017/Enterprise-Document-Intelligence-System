"""
Session management endpoint.
Handles session lifecycle operations.
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime

from app.models.requests import SessionRequest
from app.models.responses import SessionResponse
from app.memory.session_manager import get_session_manager


router = APIRouter()


@router.post("/session", response_model=SessionResponse)
async def manage_session(request: SessionRequest):
    """
    Create, retrieve, or manage a session.
    
    Operations:
    - Create new session (session_id=None)
    - Retrieve existing session (session_id provided)
    - Clear session history (clear_history=True)
    
    Args:
        request: SessionRequest with optional session_id and flags
        
    Returns:
        SessionResponse with session details
    """
    try:
        session_manager = get_session_manager()
        
        # Create new session
        if not request.session_id:
            session_id = session_manager.create_session()
            session_data = session_manager.get_session(session_id)
            
            return SessionResponse(
                session_id=session_id,
                created_at=datetime.fromisoformat(session_data["created_at"]),
                message_count=0,
                last_activity=datetime.fromisoformat(session_data["last_activity"])
            )
        
        # Get existing session
        session_data = session_manager.get_session(request.session_id)
        
        if not session_data:
            raise HTTPException(
                status_code=404,
                detail=f"Session {request.session_id} not found or expired"
            )
        
        # Clear history if requested
        if request.clear_history:
            session_manager.clear_session_history(request.session_id)
            session_data = session_manager.get_session(request.session_id)
        
        return SessionResponse(
            session_id=session_data["session_id"],
            created_at=datetime.fromisoformat(session_data["created_at"]),
            message_count=session_data["message_count"],
            last_activity=datetime.fromisoformat(session_data["last_activity"])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Session operation failed: {str(e)}"
        )


@router.get("/session/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """
    Retrieve session details by ID.
    
    Args:
        session_id: Session identifier
        
    Returns:
        SessionResponse with session details
    """
    try:
        session_manager = get_session_manager()
        session_data = session_manager.get_session(session_id)
        
        if not session_data:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found or expired"
            )
        
        return SessionResponse(
            session_id=session_data["session_id"],
            created_at=datetime.fromisoformat(session_data["created_at"]),
            message_count=session_data["message_count"],
            last_activity=datetime.fromisoformat(session_data["last_activity"])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve session: {str(e)}"
        )


@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Success message
    """
    try:
        session_manager = get_session_manager()
        success = session_manager.delete_session(session_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )
        
        return {"success": True, "message": f"Session {session_id} deleted"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete session: {str(e)}"
        )
