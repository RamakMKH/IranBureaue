"""
Authentication service with session management
"""
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict
from passlib.context import CryptContext
from config import settings

logger = logging.getLogger(__name__)


class AuthService:
    """Handles authentication and session management"""
    
    def __init__(self):
        try:
            self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        except Exception as e:
            logger.error(f"Failed to initialize bcrypt: {e}")
            raise ValueError(f"Bcrypt initialization failed. Ensure bcrypt 4.0.1+ is installed")
        
        self.admin_username = settings.ADMIN_USERNAME
        self.admin_password_hash = settings.ADMIN_PASSWORD_HASH
        self.active_sessions: Dict[str, dict] = {}
        self.session_expire_hours = settings.SESSION_EXPIRE_HOURS
    
    def verify_credentials(self, username: str, password: str) -> bool:
        """
        Verify user credentials
        
        Args:
            username: Username
            password: Plain text password
            
        Returns:
            True if credentials are valid
        """
        try:
            # Check username
            if username != self.admin_username:
                logger.warning(f"Invalid username attempt: {username}")
                return False
            
            # Verify password against stored hash
            is_valid = self.pwd_context.verify(password, self.admin_password_hash)
            
            if is_valid:
                logger.info(f"Successful login for user: {username}")
            else:
                logger.warning(f"Invalid password for user: {username}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Credential verification error: {e}")
            return False
    
    def create_session(self, username: str) -> str:
        """
        Create a new session
        
        Args:
            username: Username
            
        Returns:
            Session ID (secure token)
        """
        session_id = secrets.token_urlsafe(32)
        
        self.active_sessions[session_id] = {
            "username": username,
            "created_at": datetime.now(),
            "last_activity": datetime.now()
        }
        
        logger.info(f"Session created for user: {username}")
        return session_id
    
    def verify_session(self, session_id: str) -> Optional[str]:
        """
        Verify and update session
        
        Args:
            session_id: Session ID to verify
            
        Returns:
            Username if session is valid, None otherwise
        """
        if not session_id or session_id not in self.active_sessions:
            return None
        
        session_data = self.active_sessions[session_id]
        
        # Check expiration
        created_at = session_data["created_at"]
        age = datetime.now() - created_at
        
        if age.total_seconds() > self.session_expire_hours * 3600:
            # Session expired
            logger.info(f"Session expired: {session_id[:10]}...")
            self.destroy_session(session_id)
            return None
        
        # Update last activity
        session_data["last_activity"] = datetime.now()
        
        return session_data["username"]
    
    def destroy_session(self, session_id: str) -> bool:
        """
        Destroy a session
        
        Args:
            session_id: Session ID to destroy
            
        Returns:
            True if session was destroyed
        """
        if session_id in self.active_sessions:
            username = self.active_sessions[session_id]["username"]
            del self.active_sessions[session_id]
            logger.info(f"Session destroyed for user: {username}")
            return True
        return False
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        now = datetime.now()
        expired = []
        
        for session_id, data in self.active_sessions.items():
            age = now - data["created_at"]
            if age.total_seconds() > self.session_expire_hours * 3600:
                expired.append(session_id)
        
        for session_id in expired:
            self.destroy_session(session_id)
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")
    
    def get_active_sessions_count(self) -> int:
        """Get number of active sessions"""
        return len(self.active_sessions)
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password (utility method)
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        return self.pwd_context.hash(password)


# Singleton instance
auth_service = AuthService()