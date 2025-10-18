"""
Authentication service with session management
Handles user authentication, session creation, and session validation
"""
import secrets
import logging
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict
from app.config import settings

logger = logging.getLogger(__name__)


class AuthService:
    """
    Handles authentication and session management
    Uses bcrypt for password hashing and token-based sessions
    """
    
    def __init__(self):
        """Initialize authentication service"""
        self.admin_username = settings.ADMIN_USERNAME
        self.admin_password_hash = settings.ADMIN_PASSWORD_HASH
        self.active_sessions: Dict[str, dict] = {}
        self.session_expire_hours = settings.SESSION_EXPIRE_HOURS
        
        logger.info("🔐 AuthService initialized")
    
    def authenticate(self, username: str, password: str) -> bool:
        """
        بررسی username و password
        
        Args:
            username: نام کاربری
            password: رمز عبور (plain text)
            
        Returns:
            True اگر اعتبارسنجی موفق باشد، False در غیر این صورت
        """
        try:
            # بررسی username
            if username != self.admin_username:
                logger.warning(f"❌ Invalid username attempt: {username}")
                return False
            
            # کار با bcrypt - بررسی password با hash ذخیره شده
            password_bytes = password.encode('utf-8')
            hash_bytes = self.admin_password_hash.encode('utf-8')
            
            # برگرداندن True/False
            is_valid = bcrypt.checkpw(password_bytes, hash_bytes)
            
            if is_valid:
                logger.info(f"✅ Successful authentication for user: {username}")
            else:
                logger.warning(f"❌ Invalid password for user: {username}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
            return False
    
    def create_session(self, username: str) -> str:
        """
        ساخت token امن و ذخیره session در حافظه
        
        Args:
            username: نام کاربری برای ساخت session
            
        Returns:
            token امن (رشته تصادفی)
        """
        # ساخت token امن
        session_token = secrets.token_urlsafe(32)
        
        # ذخیره session در حافظه
        self.active_sessions[session_token] = {
            "username": username,
            "created_at": datetime.now(),
            "last_activity": datetime.now()
        }
        
        logger.info(f"✅ Session created for user: {username} (token: {session_token[:10]}...)")
        
        # برگرداندن token
        return session_token
    
    def verify_session(self, token: str) -> bool:
        """
        بررسی معتبر بودن token و چک کردن انقضا
        
        Args:
            token: Session token برای بررسی
            
        Returns:
            True اگر session معتبر باشد، False در غیر این صورت
        """
        # بررسی معتبر بودن token
        if not token or token not in self.active_sessions:
            return False
        
        session_data = self.active_sessions[token]
        
        # چک کردن انقضا
        created_at = session_data["created_at"]
        age = datetime.now() - created_at
        
        if age.total_seconds() > self.session_expire_hours * 3600:
            # Session منقضی شده
            logger.info(f"⏰ Session expired: {token[:10]}...")
            self.delete_session(token)
            # برگرداندن False
            return False
        
        # بروزرسانی آخرین فعالیت
        session_data["last_activity"] = datetime.now()
        
        # برگرداندن True
        return True
    
    def delete_session(self, session_token: str) -> bool:
        """
        حذف session (خروج از سیستم)
        
        Args:
            session_token: Session token برای حذف
            
        Returns:
            True اگر session حذف شد، False اگر وجود نداشت
        """
        if session_token in self.active_sessions:
            username = self.active_sessions[session_token]["username"]
            del self.active_sessions[session_token]
            logger.info(f"🚪 Session deleted for user: {username}")
            return True
        return False
    
    def cleanup_expired_sessions(self):
        """
        پاکسازی تمام session های منقضی شده
        این تابع باید به صورت دوره‌ای اجرا شود
        """
        now = datetime.now()
        expired = []
        
        for session_token, data in self.active_sessions.items():
            age = now - data["created_at"]
            if age.total_seconds() > self.session_expire_hours * 3600:
                expired.append(session_token)
        
        for session_token in expired:
            self.delete_session(session_token)
        
        if expired:
            logger.info(f"🧹 Cleaned up {len(expired)} expired sessions")
    
    def get_active_sessions_count(self) -> int:
        """
        دریافت تعداد session های فعال
        
        Returns:
            تعداد session های فعال
        """
        return len(self.active_sessions)
    
    def get_session_username(self, session_token: str) -> Optional[str]:
        """
        دریافت نام کاربری مرتبط با session
        
        Args:
            session_token: Session token
            
        Returns:
            نام کاربری اگر session معتبر باشد، None در غیر این صورت
        """
        if not self.verify_session(session_token):
            return None
        
        return self.active_sessions[session_token]["username"]
    
    def hash_password(self, password: str) -> str:
        """
        تبدیل password به hash با bcrypt
        (تابع کمکی برای ساخت hash برای کاربران جدید)
        
        Args:
            password: رمز عبور plain text
            
        Returns:
            رمز عبور hash شده با bcrypt
        """
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')


# ساخت نمونه واحد (Singleton)
auth_service = AuthService()