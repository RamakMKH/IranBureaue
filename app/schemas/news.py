"""
Pydantic schemas for request/response validation
Used for API input/output validation and serialization
"""
from pydantic import BaseModel, Field, validator, field_validator
from typing import Optional, List
from datetime import datetime


# ============================================
# Authentication Schemas
# ============================================

class AuthRequest(BaseModel):
    """Login request schema"""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(..., min_length=6, max_length=100, description="Password")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "admin",
                "password": "your_password"
            }
        }


# ============================================
# Crawl Schemas
# ============================================

class CrawlRequest(BaseModel):
    """Simple crawl request schema"""
    date: str = Field(..., description="Date in ISO format (YYYY-MM-DD)")
    language: str = Field(..., min_length=2, max_length=20, description="News language")
    
    @field_validator('date')
    @classmethod
    def validate_date(cls, v):
        """Validate date format"""
        try:
            datetime.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD")
    
    class Config:
        json_schema_extra = {
            "example": {
                "date": "2024-01-15",
                "language": "english"
            }
        }


class AdvancedCrawlRequest(BaseModel):
    """Advanced crawl request with date range and filters"""
    date_from: str = Field(..., description="Start date (YYYY-MM-DD)")
    date_to: str = Field(..., description="End date (YYYY-MM-DD)")
    language: str = Field(..., min_length=2, max_length=20, description="News language")
    keywords: Optional[str] = Field(None, max_length=500, description="Comma-separated keywords")
    max_pages: Optional[int] = Field(3, ge=1, le=10, description="Maximum pages to crawl")
    limit: Optional[int] = Field(20, ge=1, le=100, description="Maximum results")
    
    @field_validator('date_from', 'date_to')
    @classmethod
    def validate_dates(cls, v):
        """Validate date format"""
        try:
            datetime.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD")
    
    class Config:
        json_schema_extra = {
            "example": {
                "date_from": "2024-01-01",
                "date_to": "2024-01-07",
                "language": "english",
                "keywords": "nuclear, sanctions",
                "max_pages": 3,
                "limit": 20
            }
        }


# ============================================
# News Schemas
# ============================================

class NewsBase(BaseModel):
    """Base news schema with common fields"""
    title: str
    language: str
    url: str


class NewsCreate(NewsBase):
    """Schema for creating news"""
    highlight_text: Optional[str] = None
    published: datetime
    domain_rank: Optional[int] = None
    categories: Optional[str] = None
    sentiment: Optional[str] = None
    score: float = 0.0
    status: str = "collected"


class NewsUpdate(BaseModel):
    """Schema for updating news"""
    title: Optional[str] = None
    status: Optional[str] = None
    translated_summary: Optional[str] = None
    edited_text: Optional[str] = None
    score: Optional[float] = None


class NewsResponse(BaseModel):
    """News response schema for API"""
    id: int
    title: str
    language: str
    published: str
    highlight_text: Optional[str] = None
    status: str
    translated_summary: Optional[str] = None
    edited_text: Optional[str] = None
    score: float
    url: str
    domain_rank: Optional[int] = None
    categories: Optional[str] = None
    sentiment: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    class Config:
        from_attributes = True  # Allows creation from ORM models
        json_schema_extra = {
            "example": {
                "id": 1,
                "title": "Iran news headline",
                "language": "english",
                "published": "2024-01-15T10:30:00",
                "highlight_text": "News content here...",
                "status": "collected",
                "translated_summary": "خلاصه ترجمه شده...",
                "edited_text": "متن ویرایش شده...",
                "score": 0.85,
                "url": "https://example.com/news/123",
                "domain_rank": 1000,
                "categories": "Politics,International",
                "sentiment": "neutral"
            }
        }


class NewsListResponse(BaseModel):
    """Response for list of news"""
    total: int
    items: List[NewsResponse]
    page: int = 1
    per_page: int = 100


# ============================================
# Statistics Schemas
# ============================================

class StatsResponse(BaseModel):
    """Statistics response schema"""
    total: int
    by_status: dict
    by_language: dict
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 150,
                "by_status": {
                    "collected": 50,
                    "approved_for_translate": 30,
                    "ready_for_final": 20,
                    "published": 50
                },
                "by_language": {
                    "english": 80,
                    "french": 40,
                    "arabic": 30
                }
            }
        }


# ============================================
# Response Schemas
# ============================================

class CrawlResponse(BaseModel):
    """Crawl operation response"""
    status: str
    news_count: int
    date: Optional[str] = None
    language: str
    message: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "news_count": 25,
                "date": "2024-01-15",
                "language": "english",
                "message": "Collected 25 news articles"
            }
        }


class PublishResponse(BaseModel):
    """Publish operation response"""
    status: str
    message: str
    news_id: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "News published successfully",
                "news_id": 123
            }
        }


class ConnectionTestResponse(BaseModel):
    """Connection test response"""
    webz_io: bool
    telegram: bool
    translation: bool
    gemini_ai: bool
    timestamp: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "webz_io": True,
                "telegram": True,
                "translation": True,
                "gemini_ai": True,
                "timestamp": "2024-01-15T10:30:00"
            }
        }


# ============================================
# Error Schemas
# ============================================

class ErrorResponse(BaseModel):
    """Error response schema"""
    status: str = "error"
    message: str
    detail: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "error",
                "message": "Operation failed",
                "detail": "Database connection error"
            }
        }


class SuccessResponse(BaseModel):
    """Generic success response"""
    status: str = "success"
    message: str
    data: Optional[dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Operation completed successfully",
                "data": {}
            }
        }


# ============================================
# Log Schemas
# ============================================

class LogQueryParams(BaseModel):
    """Log query parameters"""
    lines: int = Field(50, ge=1, le=1000, description="Number of lines")
    level: str = Field("all", pattern="^(all|INFO|WARNING|ERROR)$", description="Log level")
    search: str = Field("", max_length=200, description="Search term")


class LogResponse(BaseModel):
    """Log response with statistics"""
    logs: str
    stats: dict
    
    class Config:
        json_schema_extra = {
            "example": {
                "logs": "2024-01-15 10:30:00 - INFO - Application started\n...",
                "stats": {
                    "total_lines": 1000,
                    "displayed_lines": 50,
                    "info_count": 800,
                    "warning_count": 150,
                    "error_count": 50
                }
            }
        }