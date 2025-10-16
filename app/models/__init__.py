# ============================================
# app/models/__init__.py  
# ============================================
"""
Database models
"""
from .news import News, NewsStatus, Base

__all__ = ["News", "NewsStatus", "Base"]

