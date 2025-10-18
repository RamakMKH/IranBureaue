"""
News API routes
Handles news CRUD operations and workflow management
"""
import logging
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.news import (
    NewsResponse, 
    StatsResponse, 
    PublishResponse,
    SuccessResponse,
    ErrorResponse
)
from app.repositories.news_repository import NewsRepository
from app.services.translator import translation_service
from app.services.telegram import telegram_service
from app.models.news import NewsStatus
from app.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["news"])


# ============================================
# Get News Endpoints
# ============================================

@router.get("/news", response_model=List[NewsResponse])
async def get_news(
    lang: Optional[str] = Query(None, description="Filter by language"),
    status: Optional[str] = Query(None, description="Filter by status"),
    date: Optional[str] = Query(None, description="Filter by date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=500, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    order_by: str = Query("published", regex="^(published|score|created_at)$"),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Get news articles with optional filters
    
    - **lang**: Filter by language (english, french, arabic, etc.)
    - **status**: Filter by status (collected, published, etc.)
    - **date**: Filter by publication date (YYYY-MM-DD)
    - **limit**: Maximum number of results (1-500)
    - **offset**: Offset for pagination
    - **order_by**: Sort by field (published, score, created_at)
    """
    try:
        repo = NewsRepository(db)
        
        # Parse date if provided
        date_filter = None
        if date:
            try:
                date_filter = datetime.fromisoformat(date).date()
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail="Invalid date format. Use YYYY-MM-DD"
                )
        
        # Get news
        news_list = repo.get_all(
            language=lang,
            status=status,
            date_filter=date_filter,
            limit=limit,
            offset=offset,
            order_by=order_by
        )
        
        logger.info(f"📰 Fetched {len(news_list)} news articles")
        
        # Convert to response model
        return [
            NewsResponse(
                id=n.id,
                title=n.title,
                language=n.language,
                published=n.published.isoformat(),
                highlight_text=n.highlight_text,
                status=n.status,
                translated_summary=n.translated_summary,
                edited_text=n.edited_text,
                score=n.score,
                url=n.url,
                domain_rank=n.domain_rank,
                categories=n.categories,
                sentiment=n.sentiment,
                created_at=n.created_at.isoformat() if n.created_at else None,
                updated_at=n.updated_at.isoformat() if n.updated_at else None
            )
            for n in news_list
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching news: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to fetch news articles"
        )


@router.get("/news/{news_id}", response_model=NewsResponse)
async def get_news_by_id(
    news_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Get specific news article by ID
    
    - **news_id**: News article ID
    """
    try:
        repo = NewsRepository(db)
        news = repo.get_by_id(news_id)
        
        if not news:
            raise HTTPException(
                status_code=404, 
                detail=f"News with ID {news_id} not found"
            )
        
        logger.info(f"📰 Fetched news ID {news_id}")
        
        return NewsResponse(
            id=news.id,
            title=news.title,
            language=news.language,
            published=news.published.isoformat(),
            highlight_text=news.highlight_text,
            status=news.status,
            translated_summary=news.translated_summary,
            edited_text=news.edited_text,
            score=news.score,
            url=news.url,
            domain_rank=news.domain_rank,
            categories=news.categories,
            sentiment=news.sentiment,
            created_at=news.created_at.isoformat() if news.created_at else None,
            updated_at=news.updated_at.isoformat() if news.updated_at else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching news ID {news_id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to fetch news article"
        )


@router.get("/news/search/{query}")
async def search_news(
    query: str,
    language: Optional[str] = Query(None, description="Filter by language"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Search news by title or content
    
    - **query**: Search query string
    - **language**: Optional language filter
    - **limit**: Maximum results (1-100)
    """
    try:
        repo = NewsRepository(db)
        news_list = repo.search(query, language, limit)
        
        logger.info(f"🔍 Search '{query}': found {len(news_list)} results")
        
        return [
            NewsResponse(
                id=n.id,
                title=n.title,
                language=n.language,
                published=n.published.isoformat(),
                highlight_text=n.highlight_text,
                status=n.status,
                translated_summary=n.translated_summary,
                edited_text=n.edited_text,
                score=n.score,
                url=n.url
            )
            for n in news_list
        ]
        
    except Exception as e:
        logger.error(f"❌ Search error: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Search failed"
        )


# ============================================
# Statistics Endpoints
# ============================================

@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Get news statistics
    
    Returns comprehensive statistics including:
    - Total news count
    - Count by status
    - Count by language
    """
    try:
        repo = NewsRepository(db)
        
        stats = StatsResponse(
            total=repo.count_total(),
            by_status=repo.count_by_status(),
            by_language=repo.count_by_language()
        )
        
        logger.info(f"📊 Stats fetched: {stats.total} total articles")
        return stats
        
    except Exception as e:
        logger.error(f"❌ Error fetching stats: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to fetch statistics"
        )


@router.get("/stats/detailed")
async def get_detailed_stats(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Get detailed statistics including averages and today's stats
    """
    try:
        repo = NewsRepository(db)
        
        stats = repo.get_statistics()
        today_stats = repo.get_today_stats()
        
        return {
            **stats,
            "today": today_stats
        }
        
    except Exception as e:
        logger.error(f"❌ Error fetching detailed stats: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to fetch detailed statistics"
        )


# ============================================
# Workflow Management Endpoints
# ============================================

@router.post("/approve_translate/{news_id}")
async def approve_for_translation(
    news_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Approve news for translation and start translation process
    
    - **news_id**: News article ID to approve
    """
    try:
        repo = NewsRepository(db)
        news = repo.get_by_id(news_id)
        
        if not news:
            raise HTTPException(
                status_code=404, 
                detail=f"News with ID {news_id} not found"
            )
        
        # Update status
        repo.update_status(news_id, NewsStatus.APPROVED_FOR_TRANSLATE)
        
        # Start translation
        text_to_translate = news.highlight_text or news.title
        translated = translation_service.translate(text_to_translate)
        
        if translated:
            repo.update_translation(news_id, translated, translated)
            logger.info(f"✅ News ID {news_id} translated successfully")
            
            return SuccessResponse(
                status="success",
                message="News translated and ready for review",
                data={"news_id": news_id, "translated": True}
            )
        else:
            logger.warning(f"⚠️ Translation failed for news ID {news_id}")
            
            return SuccessResponse(
                status="warning",
                message="News approved but translation failed",
                data={"news_id": news_id, "translated": False}
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error approving news for translation: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Translation process failed"
        )


@router.post("/final_approve/{news_id}")
async def final_approve(
    news_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Final approval - queue news for publishing
    
    - **news_id**: News article ID to approve
    """
    try:
        repo = NewsRepository(db)
        news = repo.get_by_id(news_id)
        
        if not news:
            raise HTTPException(
                status_code=404, 
                detail=f"News with ID {news_id} not found"
            )
        
        # Check if news has translation
        if not news.translated_summary and not news.edited_text:
            raise HTTPException(
                status_code=400,
                detail="News must be translated before final approval"
            )
        
        # Update status to publishing queue
        repo.update_status(news_id, NewsStatus.PUBLISHED_QUEUE)
        
        logger.info(f"✅ News ID {news_id} queued for publication")
        
        return SuccessResponse(
            status="success",
            message="News queued for publication",
            data={"news_id": news_id, "status": NewsStatus.PUBLISHED_QUEUE}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error approving news: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Approval failed"
        )


@router.post("/publish_now/{news_id}", response_model=PublishResponse)
async def publish_now(
    news_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Immediately publish news to Telegram
    
    - **news_id**: News article ID to publish
    """
    try:
        repo = NewsRepository(db)
        news = repo.get_by_id(news_id)
        
        if not news:
            raise HTTPException(
                status_code=404, 
                detail=f"News with ID {news_id} not found"
            )
        
        # Check if news has translation
        if not news.edited_text and not news.translated_summary:
            raise HTTPException(
                status_code=400, 
                detail="News must be translated before publishing"
            )
        
        # Create and send message
        message = telegram_service.create_news_message(news)
        success = telegram_service.send_message(message)
        
        if success:
            repo.update_status(news_id, NewsStatus.PUBLISHED)
            logger.info(f"✅ News ID {news_id} published successfully")
            
            return PublishResponse(
                status="success",
                message="News published to Telegram successfully",
                news_id=news_id
            )
        else:
            raise HTTPException(
                status_code=500, 
                detail="Failed to publish to Telegram"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error publishing news: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Publishing failed"
        )


# ============================================
# Delete Endpoints
# ============================================

@router.delete("/news/{news_id}")
async def delete_news(
    news_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Delete news article (use with caution!)
    
    - **news_id**: News article ID to delete
    """
    try:
        repo = NewsRepository(db)
        
        # Check if exists
        if not repo.exists(news_id):
            raise HTTPException(
                status_code=404, 
                detail=f"News with ID {news_id} not found"
            )
        
        # Delete
        success = repo.delete(news_id)
        
        if success:
            logger.warning(f"🗑️ News ID {news_id} deleted by {current_user}")
            
            return SuccessResponse(
                status="success",
                message=f"News ID {news_id} deleted successfully"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to delete news"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting news: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Failed to delete news"
        )


# ============================================
# Bulk Operations
# ============================================

@router.post("/bulk_update_status")
async def bulk_update_status(
    news_ids: List[int],
    new_status: str,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Bulk update status for multiple news articles
    
    - **news_ids**: List of news IDs
    - **new_status**: New status to set
    """
    try:
        # Validate status
        if new_status not in NewsStatus.all_statuses():
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {NewsStatus.all_statuses()}"
            )
        
        repo = NewsRepository(db)
        count = repo.bulk_update_status(news_ids, new_status)
        
        logger.info(f"✅ Bulk updated {count} news to status: {new_status}")
        
        return SuccessResponse(
            status="success",
            message=f"Updated {count} news articles to status: {new_status}",
            data={"count": count, "new_status": new_status}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Bulk update error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Bulk update failed"
        )