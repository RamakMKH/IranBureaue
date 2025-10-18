"""
Authentication router
Handles login, logout, and session management routes
"""
from fastapi import APIRouter, Request, Response, HTTPException, Cookie
from fastapi.responses import RedirectResponse, FileResponse
from typing import Optional
from app.config import settings
from app.schemas.news import AuthRequest
from app.services.auth import auth_service
import logging

logger = logging.getLogger(__name__)

# Create router instance - این خط خیلی مهمه!
router = APIRouter()


@router.get("/{secret_path}/")
async def login_page(secret_path: str, request: Request):
    """
    Serve login page
    
    Args:
        secret_path: Secret path segment for security
        request: FastAPI request object
        
    Returns:
        Login page HTML
    """
    # Verify secret path
    if secret_path != settings.SECRET_PATH:
        raise HTTPException(status_code=404, detail="Not found")
    
    # Serve login page
    return FileResponse("static/index.html")


@router.post("/{secret_path}/login")
async def login(
    secret_path: str,
    auth_request: AuthRequest,
    response: Response
):
    """
    Handle login request
    
    Args:
        secret_path: Secret path segment
        auth_request: Login credentials
        response: FastAPI response object
        
    Returns:
        Redirect to dashboard on success
    """
    # Verify secret path
    if secret_path != settings.SECRET_PATH:
        raise HTTPException(status_code=404, detail="Not found")
    
    # Authenticate user
    if not auth_service.authenticate(
        auth_request.username,
        auth_request.password
    ):
        logger.warning(f"❌ Failed login attempt for username: {auth_request.username}")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create session
    session_token = auth_service.create_session(auth_request.username)
    
    logger.info(f"✅ Successful login for user: {auth_request.username}")
    
    # Redirect to dashboard with session cookie
    redirect_response = RedirectResponse(
        url=f"/{settings.SECRET_PATH}/dashboard",
        status_code=303
    )
    redirect_response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=settings.USE_HTTPS,
        samesite="lax",
        max_age=settings.SESSION_EXPIRE_HOURS * 3600
    )
    
    return redirect_response


@router.get("/{secret_path}/dashboard")
async def dashboard_page(
    secret_path: str,
    request: Request,
    session_token: Optional[str] = Cookie(None)
):
    """
    Serve dashboard page
    
    Args:
        secret_path: Secret path segment
        request: FastAPI request object
        session_token: Session token from cookie
        
    Returns:
        Dashboard HTML page
    """
    # Verify secret path
    if secret_path != settings.SECRET_PATH:
        raise HTTPException(status_code=404, detail="Not found")
    
    # Verify session
    if not session_token or not auth_service.verify_session(session_token):
        logger.warning("⚠️ Unauthorized dashboard access attempt")
        return RedirectResponse(url=f"/{settings.SECRET_PATH}/", status_code=303)
    
    # Serve dashboard HTML
    return FileResponse("static/dashboard.html")


@router.get("/{secret_path}/advanced_crawl")
async def advanced_crawl_page(
    secret_path: str,
    request: Request,
    session_token: Optional[str] = Cookie(None)
):
    """
    Serve advanced crawl page
    
    Args:
        secret_path: Secret path segment
        request: FastAPI request object
        session_token: Session token from cookie
        
    Returns:
        Advanced crawl HTML page
    """
    # Verify secret path
    if secret_path != settings.SECRET_PATH:
        raise HTTPException(status_code=404, detail="Not found")
    
    # Verify session
    if not session_token or not auth_service.verify_session(session_token):
        logger.warning("⚠️ Unauthorized advanced_crawl access attempt")
        return RedirectResponse(url=f"/{settings.SECRET_PATH}/", status_code=303)
    
    # Serve advanced crawl HTML
    return FileResponse("static/advanced_crawl.html")


@router.get("/{secret_path}/logs")
async def logs_page(
    secret_path: str,
    request: Request,
    session_token: Optional[str] = Cookie(None)
):
    """
    Serve logs page
    
    Args:
        secret_path: Secret path segment
        request: FastAPI request object
        session_token: Session token from cookie
        
    Returns:
        Logs HTML page
    """
    # Verify secret path
    if secret_path != settings.SECRET_PATH:
        raise HTTPException(status_code=404, detail="Not found")
    
    # Verify session
    if not session_token or not auth_service.verify_session(session_token):
        logger.warning("⚠️ Unauthorized logs access attempt")
        return RedirectResponse(url=f"/{settings.SECRET_PATH}/", status_code=303)
    
    # Serve logs HTML
    return FileResponse("static/logs.html")


@router.post("/{secret_path}/logout")
async def logout(
    secret_path: str,
    response: Response,
    session_token: Optional[str] = Cookie(None)
):
    """
    Handle logout request
    
    Args:
        secret_path: Secret path segment
        response: FastAPI response object
        session_token: Session token from cookie
        
    Returns:
        Redirect to login page
    """
    # Verify secret path
    if secret_path != settings.SECRET_PATH:
        raise HTTPException(status_code=404, detail="Not found")
    
    # Delete session
    if session_token:
        auth_service.delete_session(session_token)
        logger.info("👋 User logged out")
    
    # Redirect to login page and clear cookie
    redirect_response = RedirectResponse(
        url=f"/{settings.SECRET_PATH}/",
        status_code=303
    )
    redirect_response.delete_cookie(key="session_token")
    
    return redirect_response


@router.get("/{secret_path}/verify-session")
async def verify_session_endpoint(
    secret_path: str,
    session_token: Optional[str] = Cookie(None)
):
    """
    Verify if session is valid (API endpoint)
    
    Args:
        secret_path: Secret path segment
        session_token: Session token from cookie
        
    Returns:
        JSON with session validity status
    """
    # Verify secret path
    if secret_path != settings.SECRET_PATH:
        raise HTTPException(status_code=404, detail="Not found")
    
    # Check session
    is_valid = False
    if session_token:
        is_valid = auth_service.verify_session(session_token)
    
    return {
        "valid": is_valid,
        "message": "Session is valid" if is_valid else "Session is invalid or expired"
    }