# ============================================
# app/repositories/__init__.py
# ============================================
"""
Data access layer - Repository pattern
"""
from .news_repository import NewsRepository

__all__ = ["NewsRepository"]