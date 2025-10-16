"""
Authentication routes
Handles login, logout, and session management
"""
import logging
from fastapi import APIRouter, HTTPException, Request, Response, Depends
from fastapi.responses import HTMLResponse, RedirectResponse

from app.schemas.news import AuthRequest
from app.services.auth import auth_service
from app.config import settings

logger = logging.getLogger(__name__)

# Use SECRET_PATH from config instead of hardcoded value
router = APIRouter(prefix=f"/{settings.SECRET_PATH}", tags=["authentication"])


def get_current_user(request: Request) -> str:
    """
    Dependency to get current authenticated user
    Raises 401 if not authenticated
    """
    session_id = request.cookies.get("session_id")
    
    if not session_id:
        # Redirect HTML requests, raise exception for API requests
        if request.headers.get("accept") and "text/html" in request.headers.get("accept"):
            raise HTTPException(status_code=303, headers={"Location": f"/{settings.SECRET_PATH}/"})
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    username = auth_service.verify_session(session_id)
    
    if not username:
        if request.headers.get("accept") and "text/html" in request.headers.get("accept"):
            raise HTTPException(status_code=303, headers={"Location": f"/{settings.SECRET_PATH}/"})
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    return username


@router.get("/", response_class=HTMLResponse)
async def login_page():
    """Serve login page"""
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Login page not found")


@router.post("/login")
async def login(auth_request: AuthRequest, response: Response):
    """
    Handle login request
    Sets secure session cookie on success
    """
    try:
        # Verify credentials
        if not auth_service.verify_credentials(auth_request.username, auth_request.password):
            logger.warning(f"Failed login attempt for: {auth_request.username}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Create session
        session_id = auth_service.create_session(auth_request.username)
        
        # Redirect to dashboard with session cookie
        redirect_response = RedirectResponse(url=f"/{settings.SECRET_PATH}/dashboard", status_code=303)
        redirect_response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            max_age=auth_service.session_expire_hours * 3600,
            secure=settings.USE_HTTPS,  # Set based on config
            samesite="lax"
        )
        
        logger.info(f"User {auth_request.username} logged in successfully")
        return redirect_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/logout")
async def logout(request: Request):
    """
    Handle logout request
    Destroys session and clears cookie
    """
    session_id = request.cookies.get("session_id")
    
    if session_id:
        auth_service.destroy_session(session_id)
    
    redirect_response = RedirectResponse(url=f"/{settings.SECRET_PATH}/", status_code=303)
    redirect_response.delete_cookie("session_id")
    
    logger.info("User logged out")
    return redirect_response


@router.get("/session-info")
async def session_info(current_user: str = Depends(get_current_user)):
    """Get current session information (for debugging)"""
    return {
        "username": current_user,
        "active_sessions": auth_service.get_active_sessions_count()
    }
