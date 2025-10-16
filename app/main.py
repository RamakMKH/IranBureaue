"""
Main FastAPI application
Lightweight entry point with all logic delegated to services
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from apscheduler.schedulers.background import BackgroundScheduler

from config import settings
from routers import auth, news, admin
from services.crawler import crawler_service
from services.translator import translation_service
from repositories.news_repository import NewsRepository
from services.telegram import telegram_service
from models.news import NewsStatus
from database import SessionLocal

# Configure logging
logging.basicConfig(
    filename=settings.LOG_FILE,
    level=getattr(logging, settings.LOG_LEVEL),
    encoding='utf-8',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Initialize scheduler
scheduler = BackgroundScheduler()


def scheduled_crawler():
    """Scheduled crawler job"""
    try:
        logger.info("Starting scheduled crawler...")
        db = SessionLocal()
        
        # Crawl multiple languages
        languages = ['english', 'french', 'arabic', 'chinese']
        for lang in languages:
            try:
                news_list = crawler_service.crawl_news(
                    db=db,
                    language=lang,
                    max_pages=3,
                    limit=50
                )
                logger.info(f"Scheduled crawl: collected {len(news_list)} news for {lang}")
            except Exception as e:
                logger.error(f"Scheduled crawl error for {lang}: {e}")
        
        db.close()
        
    except Exception as e:
        logger.error(f"Scheduled crawler failed: {e}")


def scheduled_publisher():
    """Scheduled publisher job"""
    try:
        logger.info("Starting scheduled publisher...")
        db = SessionLocal()
        repo = NewsRepository(db)
        
        # Get news ready for publishing
        ready_news = repo.get_for_publishing(limit=10)
        
        if not ready_news:
            # Check if any news is ready for final approval
            ready_news = repo.get_by_status(NewsStatus.READY_FOR_FINAL, limit=5)
            if ready_news:
                for news in ready_news:
                    repo.update_status(news.id, NewsStatus.PUBLISHED_QUEUE)
                logger.info(f"Moved {len(ready_news)} news to publishing queue")
        
        if ready_news:
            # Publish one random news
            import random
            news = random.choice(ready_news)
            
            message = telegram_service.create_news_message(news)
            success = telegram_service.send_message(message)
            
            if success:
                repo.update_status(news.id, NewsStatus.PUBLISHED)
                logger.info(f"Published news {news.id}: {news.title}")
            else:
                logger.error(f"Failed to publish news {news.id}")
        else:
            logger.info("No news available to publish")
        
        db.close()
        
    except Exception as e:
        logger.error(f"Scheduled publisher failed: {e}")


def scheduled_translator():
    """Scheduled translator job"""
    try:
        logger.info("Starting scheduled translator...")
        db = SessionLocal()
        repo = NewsRepository(db)
        
        # Get news approved for translation
        news_list = repo.get_for_translation(limit=5)
        
        for news in news_list:
            try:
                text_to_translate = news.highlight_text or news.title
                translated = translation_service.translate(text_to_translate)
                
                if translated:
                    repo.update_translation(news.id, translated, translated)
                    logger.info(f"Translated news {news.id}")
                else:
                    logger.warning(f"Translation failed for news {news.id}")
                    
            except Exception as e:
                logger.error(f"Translation error for news {news.id}: {e}")
        
        if news_list:
            logger.info(f"Translated {len(news_list)} news articles")
        
        db.close()
        
    except Exception as e:
        logger.error(f"Scheduled translator failed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info("🚀 Starting News Management System...")
    logger.info(f"📊 Environment: {'DEBUG' if settings.DEBUG else 'PRODUCTION'}")
    
    # Schedule jobs
    scheduler.add_job(
        scheduled_crawler, 
        'interval', 
        hours=settings.CRAWLER_INTERVAL_HOURS,
        id='crawler_job'
    )
    scheduler.add_job(
        scheduled_publisher, 
        'interval', 
        minutes=settings.PUBLISHER_INTERVAL_MINUTES,
        id='publisher_job'
    )
    scheduler.add_job(
        scheduled_translator,
        'interval',
        minutes=30,
        id='translator_job'
    )
    
    scheduler.start()
    logger.info("✅ Scheduled jobs started")
    
    # Test connections
    try:
        telegram_status = telegram_service.test_connection()
        logger.info(f"📱 Telegram: {'✅ Connected' if telegram_status else '❌ Failed'}")
    except Exception as e:
        logger.warning(f"⚠️ Telegram test failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down News Management System...")
    scheduler.shutdown()
    logger.info("✅ Scheduler stopped")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Professional news management and publishing system",
    version="2.0.0",
    lifespan=lifespan
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(auth.router)
app.include_router(news.router)
app.include_router(admin.router)


@app.get("/")
async def root():
    """Root endpoint - redirect to login"""
    from fastapi.responses import RedirectResponse
    # Use the secret path from config
    return RedirectResponse(url=f"/{settings.SECRET_PATH}/")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": "2.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    import os
    
    # Get SSL configuration from environment or config
    ssl_cert_path = os.getenv("SSL_CERT_PATH", "")
    ssl_key_path = os.getenv("SSL_KEY_PATH", "")
    
    use_ssl = os.path.exists(ssl_key_path) and os.path.exists(ssl_cert_path)
    
    # Get host and port from environment or use defaults
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", "8000"))
    
    if use_ssl:
        logger.info(f"🔒 Starting with SSL/HTTPS on {host}:{port}")
        uvicorn.run(
            app,
            host=host,
            port=port,
            ssl_keyfile=ssl_key_path,
            ssl_certfile=ssl_cert_path
        )
    else:
        logger.warning(f"⚠️ SSL certificates not found, starting HTTP on {host}:{port}")
        uvicorn.run(
            app,
            host=host,
            port=port
        )
