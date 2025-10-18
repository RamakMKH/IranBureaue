"""
Admin routes
Handles crawling, publishing, logs, and system operations
"""
import os
import logging
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.news import (
    CrawlRequest, 
    AdvancedCrawlRequest, 
    CrawlResponse, 
    ConnectionTestResponse,
    SuccessResponse
)
from app.services.crawler import async_crawler_service
from app.services.telegram import telegram_service
from app.services.translator import translation_service
from app.repositories.news_repository import NewsRepository
from app.models.news import NewsStatus
from app.dependencies import get_current_user
from app.utils.logging import LogAnalyzer
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pnl7a3d", tags=["admin"])


# ============================================
# HTML Pages
# ============================================

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(current_user: str = Depends(get_current_user)):
    """
    Serve dashboard page
    Main admin panel for news management
    """
    try:
        with open("static/dashboard.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        logger.error("❌ Dashboard page not found")
        raise HTTPException(
            status_code=500, 
            detail="Dashboard page not found"
        )


@router.get("/advanced_crawl", response_class=HTMLResponse)
async def advanced_crawl_page(current_user: str = Depends(get_current_user)):
    """
    Serve advanced crawl page
    Page for advanced crawler with date range and keywords
    """
    try:
        with open("static/advanced_crawl.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        logger.error("❌ Advanced crawl page not found")
        raise HTTPException(
            status_code=500, 
            detail="Advanced crawl page not found"
        )


@router.get("/logs_page", response_class=HTMLResponse)
async def logs_page(current_user: str = Depends(get_current_user)):
    """
    Serve logs page
    Page for viewing and managing system logs
    """
    try:
        with open("static/logs.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        logger.error("❌ Logs page not found")
        raise HTTPException(
            status_code=500, 
            detail="Logs page not found"
        )


# ============================================
# Crawl Operations
# ============================================

@router.post("/crawl_by_date", response_model=CrawlResponse)
async def crawl_by_date(
    crawl_request: CrawlRequest,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Simple crawl by date and language
    
    - **date**: Date in YYYY-MM-DD format
    - **language**: News language (english, french, arabic, etc.)
    """
    try:
        logger.info(
            f"🕷️ Starting crawl for {crawl_request.language} "
            f"on {crawl_request.date} by {current_user}"
        )
        
        news_list = async_crawler_service.crawl_news(
            db=db,
            language=crawl_request.language,
            specific_date=crawl_request.date,
            max_pages=settings.CRAWLER_MAX_PAGES,
            limit=settings.CRAWLER_MAX_RESULTS
        )
        
        logger.info(f"✅ Crawl completed: {len(news_list)} articles collected")
        
        return CrawlResponse(
            status="success",
            news_count=len(news_list),
            date=crawl_request.date,
            language=crawl_request.language,
            message=f"Collected {len(news_list)} news articles successfully"
        )
        
    except Exception as e:
        logger.error(f"❌ Crawl error: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Crawl failed: {str(e)}"
        )


@router.post("/advanced_crawl")
async def advanced_crawl(
    crawl_request: AdvancedCrawlRequest,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Advanced crawl with date range and keywords
    
    - **date_from**: Start date (YYYY-MM-DD)
    - **date_to**: End date (YYYY-MM-DD)
    - **language**: News language
    - **keywords**: Optional comma-separated keywords
    - **max_pages**: Maximum pages per day (1-10)
    - **limit**: Maximum total results (1-100)
    """
    try:
        # Parse dates
        date_from = datetime.fromisoformat(crawl_request.date_from)
        date_to = datetime.fromisoformat(crawl_request.date_to)
        
        # Validate date range
        if date_from > date_to:
            raise HTTPException(
                status_code=400, 
                detail="Start date must be before end date"
            )
        
        if (date_to - date_from).days > 30:
            raise HTTPException(
                status_code=400, 
                detail="Date range cannot exceed 30 days"
            )
        
        logger.info(
            f"🕷️ Advanced crawl started: {date_from.date()} to {date_to.date()} "
            f"({crawl_request.language}) by {current_user}"
        )
        
        if crawl_request.keywords:
            logger.info(f"🔍 Keywords: {crawl_request.keywords}")
        
        news_list = async_crawler_service.advanced_crawl(
            db=db,
            date_from=date_from,
            date_to=date_to,
            language=crawl_request.language,
            keywords=crawl_request.keywords,
            max_pages=crawl_request.max_pages,
            limit=crawl_request.limit
        )
        
        logger.info(f"✅ Advanced crawl completed: {len(news_list)} articles")
        
        # Return detailed response
        return {
            "status": "success",
            "news_count": len(news_list),
            "date_range": {
                "from": crawl_request.date_from,
                "to": crawl_request.date_to
            },
            "language": crawl_request.language,
            "keywords": crawl_request.keywords,
            "news": [
                {
                    "id": n.id,
                    "title": n.title,
                    "language": n.language,
                    "published": n.published.isoformat(),
                    "highlight_text": (
                        n.highlight_text[:200] + "..." 
                        if n.highlight_text and len(n.highlight_text) > 200 
                        else n.highlight_text
                    ),
                    "status": n.status,
                    "score": n.score,
                    "url": n.url
                }
                for n in news_list
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Advanced crawl error: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Advanced crawl failed: {str(e)}"
        )


# ============================================
# Publishing Operations
# ============================================

@router.post("/publish_news")
async def trigger_publish_news(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Manually trigger news publishing
    Publishes one news from the queue
    """
    try:
        repo = NewsRepository(db)
        
        # Get news ready for publishing
        ready_news = repo.get_for_publishing(limit=10)
        
        if not ready_news:
            # If no news in queue, check ready_for_final
            ready_news = repo.get_by_status(NewsStatus.READY_FOR_FINAL, limit=5)
            
            if ready_news:
                # Move to queue
                for news in ready_news:
                    repo.update_status(news.id, NewsStatus.PUBLISHED_QUEUE)
                
                logger.info(f"📋 Moved {len(ready_news)} news to publishing queue")
                
                return SuccessResponse(
                    status="success",
                    message=f"Moved {len(ready_news)} news to publishing queue",
                    data={"moved_to_queue": len(ready_news)}
                )
        
        if not ready_news:
            logger.info("⚠️ No news available to publish")
            return SuccessResponse(
                status="info",
                message="No news available to publish"
            )
        
        # Publish random news from queue
        import random
        news = random.choice(ready_news)
        
        message = telegram_service.create_news_message(news)
        success = telegram_service.send_message(message)
        
        if success:
            repo.update_status(news.id, NewsStatus.PUBLISHED)
            logger.info(f"✅ Published news ID {news.id}: {news.title[:50]}")
            
            return SuccessResponse(
                status="success",
                message=f"News published successfully",
                data={
                    "news_id": news.id,
                    "title": news.title[:100]
                }
            )
        else:
            logger.error(f"❌ Failed to publish news ID {news.id}")
            raise HTTPException(
                status_code=500, 
                detail="Failed to publish to Telegram"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Publishing error: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Publishing failed: {str(e)}"
        )


@router.post("/auto_translate_pending")
async def auto_translate_pending(
    limit: int = Query(5, ge=1, le=20, description="Number of articles to translate"),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Automatically translate pending approved news
    Useful for batch translation
    """
    try:
        repo = NewsRepository(db)
        
        # Get news approved for translation
        pending_news = repo.get_for_translation(limit=limit)
        
        if not pending_news:
            return SuccessResponse(
                status="info",
                message="No news pending translation"
            )
        
        translated_count = 0
        failed_count = 0
        
        for news in pending_news:
            try:
                text_to_translate = news.highlight_text or news.title
                translated = translation_service.translate(text_to_translate)
                
                if translated:
                    repo.update_translation(news.id, translated, translated)
                    translated_count += 1
                    logger.info(f"✅ Translated news ID {news.id}")
                else:
                    failed_count += 1
                    logger.warning(f"⚠️ Translation failed for news ID {news.id}")
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"❌ Translation error for news ID {news.id}: {e}")
        
        logger.info(
            f"📊 Auto-translation completed: "
            f"{translated_count} success, {failed_count} failed"
        )
        
        return SuccessResponse(
            status="success",
            message=f"Translated {translated_count} news articles",
            data={
                "translated": translated_count,
                "failed": failed_count,
                "total": len(pending_news)
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Auto-translation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Auto-translation failed: {str(e)}"
        )


# ============================================
# FIXED: Logs Operations Section
# ============================================

@router.get("/logs")
async def get_logs(current_user: str = Depends(get_current_user)):
    """
    Get recent logs (simple version)
    Returns last 50 lines of log file
    """
    try:
        if not os.path.exists(settings.LOG_FILE):
            return "Log file not found"
        
        with open(settings.LOG_FILE, "r", encoding="utf-8") as f:
            logs = f.readlines()[-50:]  # ← FIXED: Get last 50 lines
            return "".join(logs)
        
    except Exception as e:
        logger.error(f"❌ Error reading logs: {e}")
        return f"Error reading logs: {str(e)}"


@router.get("/logs_advanced")
async def get_logs_advanced(
    lines: int = Query(50, ge=1, le=1000),
    level: str = Query("all", regex="^(all|INFO|WARNING|ERROR)$"),
    search: str = Query("", max_length=200),
    current_user: str = Depends(get_current_user)
):
    """
    Get logs with advanced filtering
    
    - **lines**: Number of lines to return (1-1000)
    - **level**: Filter by log level (all, INFO, WARNING, ERROR)
    - **search**: Search term to filter logs
    """
    try:
        if not os.path.exists(settings.LOG_FILE):
            return {
                "logs": "Log file not found",
                "stats": {}
            }
        
        # Use LogAnalyzer for advanced features
        analyzer = LogAnalyzer(settings.LOG_FILE)
        
        # Get filtered logs
        if search:
            logs = analyzer.search_logs(search, max_lines=lines)
        else:
            logs = analyzer.get_recent_logs(lines=lines, level=level if level != "all" else None)
        
        # Get statistics
        stats = analyzer.get_log_stats()
        
        return {
            "logs": "\n".join(logs),
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"❌ Error reading advanced logs: {e}")
        return {
            "logs": f"Error: {str(e)}",
            "stats": {}
        }


@router.delete("/clear_logs")
async def clear_logs(
    keep_lines: int = Query(100, ge=0, le=1000),
    current_user: str = Depends(get_current_user)
):
    """
    Clear log file, optionally keeping recent lines
    
    - **keep_lines**: Number of recent lines to keep (0 to clear all)
    """
    try:
        if not os.path.exists(settings.LOG_FILE):
            return SuccessResponse(
                status="info",
                message="Log file does not exist"
            )
        
        if keep_lines > 0:
            # Keep recent lines
            with open(settings.LOG_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
                keep = lines[-keep_lines:]
            
            with open(settings.LOG_FILE, "w", encoding="utf-8") as f:
                f.writelines(keep)
            
            logger.warning(f"🗑️ Logs cleared, kept last {keep_lines} lines by {current_user}")
            
            return SuccessResponse(
                status="success",
                message=f"Cleared logs, kept {keep_lines} recent lines"
            )
        else:
            # Clear all
            with open(settings.LOG_FILE, "w", encoding="utf-8") as f:
                f.write("")
            
            logger.warning(f"🗑️ All logs cleared by {current_user}")
            
            return SuccessResponse(
                status="success",
                message="All logs cleared"
            )
        
    except Exception as e:
        logger.error(f"❌ Error clearing logs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear logs: {str(e)}"
        )


# ============================================
# FIXED: Test Connection Function
# ============================================

@router.get("/test_connection")
async def test_connection(current_user: str = Depends(get_current_user)):
    """
    Test connections to external services
    Tests: Webz.io, Telegram, Translation, Gemini AI
    """
    try:
        logger.info("🔌 Testing connections to external services...")
        
        # Test Webz.io
        webz_status = False
        try:
            from app.utils.proxy import async_proxy_manager as proxy_manager
            session = proxy_manager.create_session(timeout=10)
            test_url = (
                f"https://api.webz.io/newsApiLite?"
                f"token={settings.WEBZ_API_KEYS[0] if settings.WEBZ_API_KEYS else 'test'}&"
                f"q=test&language=english&size=1"
            )
            response = session.get(test_url, timeout=10)
            webz_status = response.status_code == 200
            logger.info(f"🌐 Webz.io: {'✅ OK' if webz_status else '❌ Failed'}")
        except Exception as e:
            logger.error(f"❌ Webz.io test failed: {e}")
        
        # Test Telegram
        telegram_status = False
        try:
            telegram_status = telegram_service.test_connection()
            logger.info(f"📱 Telegram: {'✅ OK' if telegram_status else '❌ Failed'}")
        except Exception as e:
            logger.error(f"❌ Telegram test failed: {e}")
        
        # Test Translation
        translation_status = False
        try:
            test_text = translation_service.translate("Hello", "fa")
            translation_status = bool(test_text)
            logger.info(f"🌐 Translation: {'✅ OK' if translation_status else '❌ Failed'}")
        except Exception as e:
            logger.error(f"❌ Translation test failed: {e}")
        
        # Test Gemini AI
        gemini_status = False
        if settings.GEMINI_API_KEYS and settings.GEMINI_API_KEYS[0]:
            try:
                from app.utils.proxy import async_proxy_manager as proxy_manager
                session = proxy_manager.create_session(timeout=10)
                url = "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent"
                params = {"key": settings.GEMINI_API_KEYS[0]}
                payload = {
                    "contents": [{
                        "parts": [{"text": "Say OK only"}]
                    }]
                }
                response = session.post(url, params=params, json=payload, timeout=10)
                gemini_status = response.status_code == 200
                logger.info(f"🤖 Gemini AI: {'✅ OK' if gemini_status else '❌ Failed'}")
            except Exception as e:
                logger.error(f"❌ Gemini test failed: {e}")
        
        return ConnectionTestResponse(
            webz_io=webz_status,
            telegram=telegram_status,
            translation=translation_status,
            gemini_ai=gemini_status,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"❌ Connection test error: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Connection test failed"
        )
        
# ============================================
# Maintenance & Utilities
# ============================================

@router.post("/cleanup_old_news")
async def cleanup_old_news(
    days: int = Query(90, ge=30, le=365, description="Keep news newer than X days"),
    dry_run: bool = Query(True, description="Dry run mode (don't delete)"),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Cleanup old published news
    
    - **days**: Keep news newer than this many days (30-365)
    - **dry_run**: If true, only count without deleting
    """
    try:
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Find old published news
        old_news = db.query(News).filter(
            News.status == NewsStatus.PUBLISHED,
            News.published < cutoff_date
        ).all()
        
        count = len(old_news)
        
        if dry_run:
            logger.info(f"🔍 Dry run: Found {count} old news articles (>{days} days)")
            return SuccessResponse(
                status="info",
                message=f"Found {count} old news articles",
                data={
                    "count": count,
                    "dry_run": True,
                    "cutoff_date": cutoff_date.isoformat()
                }
            )
        else:
            # Actually delete
            repo = NewsRepository(db)
            news_ids = [n.id for n in old_news]
            deleted = repo.bulk_delete(news_ids)
            
            logger.warning(
                f"🗑️ Deleted {deleted} old news articles (>{days} days) "
                f"by {current_user}"
            )
            
            return SuccessResponse(
                status="success",
                message=f"Deleted {deleted} old news articles",
                data={
                    "deleted": deleted,
                    "cutoff_date": cutoff_date.isoformat()
                }
            )
        
    except Exception as e:
        logger.error(f"❌ Cleanup error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Cleanup failed: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    Health check endpoint (no authentication required)
    Useful for monitoring and load balancers
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "News Management System",
        "version": "2.0.0"
    }

async def test_connection(current_user: str = Depends(get_current_user)):
    """
    Test connections to external services
    Tests: Webz.io, Telegram, Translation, Gemini AI
    """
    try:
        logger.info("🔌 Testing connections to external services...")
        
        # Test Webz.io
        webz_status = False
        try:
            from app.utils.proxy import async_proxy_manager as proxy_manager
            session = proxy_manager.create_session(timeout=10)
            test_url = (
                f"https://api.webz.io/newsApiLite?"
                f"token={settings.WEBZ_API_KEYS[0]}&q=test&"
                f"ts={int(datetime.now().timestamp() * 1000)}"
            )
            response = session.get(test_url, timeout=10)
            webz_status = response.status_code == 200
            logger.info(f"📡 Webz.io: {'✅ OK' if webz_status else '❌ Failed'}")
        except Exception as e:
            logger.error(f"❌ Webz.io test failed: {e}")
        
        # Test Telegram
        telegram_status = telegram_service.test_connection()
        logger.info(f"📱 Telegram: {'✅ OK' if telegram_status else '❌ Failed'}")
        
        # Test Translation
        translation_status = False
        try:
            test_text = translation_service.translate("Hello, this is a test.", "fa")
            translation_status = bool(test_text)
            logger.info(f"🌐 Translation: {'✅ OK' if translation_status else '❌ Failed'}")
        except Exception as e:
            logger.error(f"❌ Translation test failed: {e}")
        
        # Test Gemini AI
        gemini_status = False
        if settings.GEMINI_API_KEYS and settings.GEMINI_API_KEYS[0]:
            try:
                from app.utils.proxy import async_proxy_manager as proxy_manager
                session = proxy_manager.create_session(timeout=10)
                url = "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent"
                params = {"key": settings.GEMINI_API_KEYS[0]}
                payload = {
                    "contents": [{
                        "parts": [{"text": "Say OK only"}]
                    }]
                }
                response = session.post(url, params=params, json=payload, timeout=10)
                gemini_status = response.status_code == 200
                logger.info(f"🤖 Gemini AI: {'✅ OK' if gemini_status else '❌ Failed'}")
            except Exception as e:
                logger.error(f"❌ Gemini test failed: {e}")
        
        return ConnectionTestResponse(
            webz_io=webz_status,
            telegram=telegram_status,
            translation=translation_status,
            gemini_ai=gemini_status,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"❌ Connection test error: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Connection test failed"
        )


@router.get("/system_info")
async def get_system_info(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Get system information and statistics
    """
    try:
        repo = NewsRepository(db)
        
        # Get crawler status
        crawler_status = async_crawler_service.get_api_status()
        
        # Get repository stats
        repo_stats = repo.get_statistics()
        today_stats = repo.get_today_stats()
        
        return {
            "system": {
                "version": "2.0.0",
                "environment": "production" if not settings.DEBUG else "development",
                "uptime": "N/A"  # Can be implemented with process tracking
            },
            "crawler": crawler_status,
            "statistics": {
                **repo_stats,
                "today": today_stats
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ System info error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get system information"
        )
