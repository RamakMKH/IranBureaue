"""
FastAPI dependencies
Common dependencies for route handlers
"""
from typing import Generator
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.services.auth import auth_service


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
    session_id = request.cookies.get("session_id")
    
    if not session_id:
        # Check if HTML request (browser) or API request
        accept_header = request.headers.get("accept", "")
        if "text/html" in accept_header:
            # Redirect to login page
            raise HTTPException(
                status_code=303,
                headers={"Location": "/pnl7a3d/"}
            )
        else:
            # Return 401 for API requests
            raise HTTPException(
                status_code=401,
                detail="Not authenticated"
            )
    
    # Verify session
    username = auth_service.verify_session(session_id)
    
    if not username:
        accept_header = request.headers.get("accept", "")
        if "text/html" in accept_header:
            raise HTTPException(
                status_code=303,
                headers={"Location": "/pnl7a3d/"}
            )
        else:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired session"
            )
    
    return username


def get_optional_user(request: Request) -> str | None:
    """
    Optional authentication dependency
    Returns username if authenticated, None otherwise
    Does not raise exceptions
    
    Usage:
        @app.get("/endpoint")
        def endpoint(current_user: str | None = Depends(get_optional_user)):
            if current_user:
                # User is authenticated
            else:
                # Anonymous access
    """
    session_id = request.cookies.get("session_id")
    
    if not session_id:
        return None
    
    return auth_service.verify_session(session_id)