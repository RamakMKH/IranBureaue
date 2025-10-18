"""
FastAPI dependencies
Common dependencies for route handlers
"""
from typing import Generator, Optional
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.services.auth import auth_service
from app.config import settings


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency
    
    Usage:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            # Use db here
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(request: Request) -> str:
    """
    Authentication dependency
    Returns current authenticated username
    Raises 401 if not authenticated
    
    Usage:
        @app.get("/endpoint")
        def endpoint(current_user: str = Depends(get_current_user)):
            # User is authenticated
    """
    # Get session token from cookie (correct name!)
    session_token = request.cookies.get("session_token")
    
    if not session_token:
        # Check if HTML request (browser) or API request
        accept_header = request.headers.get("accept", "")
        if "text/html" in accept_header:
            # Redirect to login page with correct SECRET_PATH
            raise HTTPException(
                status_code=303,
                headers={"Location": f"/{settings.SECRET_PATH}/"}
            )
        else:
            # Return 401 for API requests
            raise HTTPException(
                status_code=401,
                detail="Not authenticated"
            )
    
    # Verify session (returns True/False)
    is_valid = auth_service.verify_session(session_token)
    
    if not is_valid:
        accept_header = request.headers.get("accept", "")
        if "text/html" in accept_header:
            raise HTTPException(
                status_code=303,
                headers={"Location": f"/{settings.SECRET_PATH}/"}
            )
        else:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired session"
            )
    
    # Get username from session
    username = auth_service.get_session_username(session_token)
    
    if not username:
        raise HTTPException(
            status_code=401,
            detail="Session error"
        )
    
    return username


def get_optional_user(request: Request) -> Optional[str]:
    """
    Optional authentication dependency
    Returns username if authenticated, None otherwise
    Does not raise exceptions
    
    Usage:
        @app.get("/endpoint")
        def endpoint(current_user: Optional[str] = Depends(get_optional_user)):
            if current_user:
                # User is authenticated
            else:
                # Anonymous access
    """
    # Get session token from cookie
    session_token = request.cookies.get("session_token")
    
    if not session_token:
        return None
    
    # Verify session
    is_valid = auth_service.verify_session(session_token)
    
    if not is_valid:
        return None
    
    # Get username
    return auth_service.get_session_username(session_token)