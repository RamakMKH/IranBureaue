# ============================================
# app/schemas/__init__.py
# ============================================
"""
Pydantic schemas for request/response validation
"""
from .news import (
    AuthRequest,
    CrawlRequest,
    AdvancedCrawlRequest,
    NewsResponse,
    StatsResponse,
    CrawlResponse,
    ConnectionTestResponse
)

__all__ = [
    "AuthRequest",
    "CrawlRequest",
    "AdvancedCrawlRequest",
    "NewsResponse",
    "StatsResponse",
    "CrawlResponse",
    "ConnectionTestResponse"
]

