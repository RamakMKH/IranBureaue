"""
Repository pattern for News database operations
Separates data access logic from business logic
Provides clean interface for database operations
"""
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from datetime import datetime, date, timedelta
from app.models.news import News, NewsStatus

logger = logging.getLogger(__name__)


class NewsRepository:
    """
    Repository for News database operations
    Implements Repository pattern for clean separation of concerns
    """
    
    def __init__(self, db: Session):
        """
        Initialize repository with database session
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
    
    # ============================================
    # Create Operations
    # ============================================
    
    def create(self, news: News) -> News:
        """
        Create a new news article
        
        Args:
            news: News object to create
            
        Returns:
            Created News object with ID
        """
        try:
            self.db.add(news)
            self.db.commit()
            self.db.refresh(news)
            logger.debug(f"➕ Created news ID {news.id}: {news.title[:50]}")
            return news
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error creating news: {e}")
            raise
    
    def bulk_create(self, news_list: List[News]) -> int:
        """
        Create multiple news articles in bulk
        
        Args:
            news_list: List of News objects
            
        Returns:
            Number of created articles
        """
        try:
            self.db.bulk_save_objects(news_list)
            self.db.commit()
            count = len(news_list)
            logger.info(f"➕ Bulk created {count} news articles")
            return count
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error bulk creating news: {e}")
            raise
    
    # ============================================
    # Read Operations
    # ============================================
    
    def get_by_id(self, news_id: int) -> Optional[News]:
        """
        Get news by ID
        
        Args:
            news_id: News ID
            
        Returns:
            News object or None if not found
        """
        return self.db.query(News).filter(News.id == news_id).first()
    
    def get_by_url(self, url: str) -> Optional[News]:
        """
        Get news by URL (useful for duplicate checking)
        
        Args:
            url: News URL
            
        Returns:
            News object or None
        """
        return self.db.query(News).filter(News.url == url).first()
    
    def get_all(
        self, 
        language: Optional[str] = None,
        status: Optional[str] = None,
        date_filter: Optional[date] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "published"
    ) -> List[News]:
        """
        Get all news with optional filters
        
        Args:
            language: Filter by language
            status: Filter by status
            date_filter: Filter by publication date
            limit: Maximum results
            offset: Offset for pagination
            order_by: Field to order by (published, score, created_at)
            
        Returns:
            List of News objects
        """
        query = self.db.query(News)
        
        # Apply filters
        if language:
            query = query.filter(News.language == language)
        if status:
            query = query.filter(News.status == status)
        if date_filter:
            query = query.filter(func.date(News.published) == date_filter)
        
        # Apply ordering
        if order_by == "score":
            query = query.order_by(desc(News.score))
        elif order_by == "created_at":
            query = query.order_by(desc(News.created_at))
        else:  # Default: published
            query = query.order_by(desc(News.published))
        
        # Apply pagination
        return query.limit(limit).offset(offset).all()
    
    def get_by_status(self, status: str, limit: int = 100) -> List[News]:
        """
        Get news by status, ordered by score
        
        Args:
            status: News status
            limit: Maximum results
            
        Returns:
            List of News objects
        """
        return self.db.query(News).filter(
            News.status == status
        ).order_by(desc(News.score)).limit(limit).all()
    
    def get_for_translation(self, limit: int = 10) -> List[News]:
        """
        Get news ready for translation
        
        Args:
            limit: Maximum results
            
        Returns:
            List of News objects awaiting translation
        """
        return self.db.query(News).filter(
            News.status == NewsStatus.APPROVED_FOR_TRANSLATE
        ).order_by(desc(News.score)).limit(limit).all()
    
    def get_for_publishing(self, limit: int = 10) -> List[News]:
        """
        Get news ready for publishing
        
        Args:
            limit: Maximum results
            
        Returns:
            List of News objects in publishing queue
        """
        return self.db.query(News).filter(
            News.status == NewsStatus.PUBLISHED_QUEUE
        ).order_by(desc(News.published)).limit(limit).all()
    
    def get_recent_for_duplicate_check(self, days: int = 7) -> List[News]:
        """
        Get recent news for duplicate checking
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of recent News objects
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return self.db.query(News).filter(
            News.published >= cutoff_date
        ).all()
    
    def get_high_score_news(self, threshold: float = 0.7, limit: int = 20) -> List[News]:
        """
        Get high-scoring news articles
        
        Args:
            threshold: Minimum score threshold
            limit: Maximum results
            
        Returns:
            List of high-scoring News objects
        """
        return self.db.query(News).filter(
            News.score >= threshold
        ).order_by(desc(News.score)).limit(limit).all()
    
    def search(
        self, 
        query: str, 
        language: Optional[str] = None,
        limit: int = 50
    ) -> List[News]:
        """
        Search news by title or content
        
        Args:
            query: Search query string
            language: Optional language filter
            limit: Maximum results
            
        Returns:
            List of matching News objects
        """
        search_filter = or_(
            News.title.ilike(f"%{query}%"),
            News.highlight_text.ilike(f"%{query}%"),
            News.translated_summary.ilike(f"%{query}%")
        )
        
        if language:
            search_filter = and_(search_filter, News.language == language)
        
        return self.db.query(News).filter(
            search_filter
        ).order_by(desc(News.score)).limit(limit).all()
    
    # ============================================
    # Update Operations
    # ============================================
    
    def update(self, news_id: int, **kwargs) -> bool:
        """
        Update news fields
        
        Args:
            news_id: News ID
            **kwargs: Fields to update
            
        Returns:
            True if updated successfully
        """
        try:
            news = self.get_by_id(news_id)
            if not news:
                logger.warning(f"⚠️ News ID {news_id} not found for update")
                return False
            
            for key, value in kwargs.items():
                if hasattr(news, key):
                    setattr(news, key, value)
            
            news.updated_at = datetime.utcnow()
            self.db.commit()
            logger.debug(f"✏️ Updated news ID {news_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error updating news ID {news_id}: {e}")
            return False
    
    def update_status(self, news_id: int, status: str) -> bool:
        """
        Update news status
        
        Args:
            news_id: News ID
            status: New status
            
        Returns:
            True if updated successfully
        """
        try:
            news = self.get_by_id(news_id)
            if not news:
                logger.warning(f"⚠️ News ID {news_id} not found")
                return False
            
            old_status = news.status
            news.status = status
            news.updated_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"📝 News ID {news_id}: {old_status} → {status}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error updating status for news ID {news_id}: {e}")
            return False
    
    def update_translation(
        self, 
        news_id: int, 
        translated_summary: str, 
        edited_text: str
    ) -> bool:
        """
        Update news translation
        
        Args:
            news_id: News ID
            translated_summary: Translated summary text
            edited_text: Edited text
            
        Returns:
            True if updated successfully
        """
        try:
            news = self.get_by_id(news_id)
            if not news:
                logger.warning(f"⚠️ News ID {news_id} not found")
                return False
            
            news.translated_summary = translated_summary
            news.edited_text = edited_text
            news.status = NewsStatus.READY_FOR_FINAL
            news.updated_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"🌐 Translation updated for news ID {news_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error updating translation for news ID {news_id}: {e}")
            return False
    
    def bulk_update_status(self, news_ids: List[int], status: str) -> int:
        """
        Bulk update status for multiple news
        
        Args:
            news_ids: List of news IDs
            status: New status
            
        Returns:
            Number of updated records
        """
        try:
            count = self.db.query(News).filter(
                News.id.in_(news_ids)
            ).update(
                {
                    News.status: status, 
                    News.updated_at: datetime.utcnow()
                },
                synchronize_session=False
            )
            self.db.commit()
            logger.info(f"📝 Bulk updated {count} news to status: {status}")
            return count
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error bulk updating status: {e}")
            return 0
    
    # ============================================
    # Delete Operations
    # ============================================
    
    def delete(self, news_id: int) -> bool:
        """
        Delete news (use with caution!)
        
        Args:
            news_id: News ID to delete
            
        Returns:
            True if deleted successfully
        """
        try:
            news = self.get_by_id(news_id)
            if not news:
                logger.warning(f"⚠️ News ID {news_id} not found for deletion")
                return False
            
            self.db.delete(news)
            self.db.commit()
            logger.warning(f"🗑️ Deleted news ID {news_id}: {news.title[:50]}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error deleting news ID {news_id}: {e}")
            return False
    
    def bulk_delete(self, news_ids: List[int]) -> int:
        """
        Bulk delete multiple news articles
        
        Args:
            news_ids: List of news IDs to delete
            
        Returns:
            Number of deleted records
        """
        try:
            count = self.db.query(News).filter(
                News.id.in_(news_ids)
            ).delete(synchronize_session=False)
            self.db.commit()
            logger.warning(f"🗑️ Bulk deleted {count} news articles")
            return count
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error bulk deleting news: {e}")
            return 0
    
    # ============================================
    # Statistics & Analytics
    # ============================================
    
    def count_total(self) -> int:
        """
        Count total news articles
        
        Returns:
            Total count
        """
        return self.db.query(func.count(News.id)).scalar()
    
    def count_by_status(self) -> dict:
        """
        Count news by status
        
        Returns:
            Dictionary of status counts
        """
        result = self.db.query(
            News.status, 
            func.count(News.id)
        ).group_by(News.status).all()
        
        return dict(result)
    
    def count_by_language(self) -> dict:
        """
        Count news by language
        
        Returns:
            Dictionary of language counts
        """
        result = self.db.query(
            News.language, 
            func.count(News.id)
        ).group_by(News.language).all()
        
        return dict(result)
    
    def get_average_score(self) -> float:
        """
        Get average score of all news
        
        Returns:
            Average score
        """
        avg = self.db.query(func.avg(News.score)).scalar()
        return round(float(avg), 3) if avg else 0.0
    
    def get_statistics(self) -> dict:
        """
        Get comprehensive statistics
        
        Returns:
            Dictionary with various statistics
        """
        return {
            "total": self.count_total(),
            "by_status": self.count_by_status(),
            "by_language": self.count_by_language(),
            "average_score": self.get_average_score(),
            "high_score_count": len(self.get_high_score_news(threshold=0.7, limit=1000))
        }
    
    def get_today_stats(self) -> dict:
        """
        Get statistics for today's news
        
        Returns:
            Dictionary with today's statistics
        """
        today = datetime.utcnow().date()
        today_news = self.db.query(News).filter(
            func.date(News.created_at) == today
        ).all()
        
        return {
            "total_today": len(today_news),
            "by_status": {
                status: len([n for n in today_news if n.status == status])
                for status in NewsStatus.all_statuses()
            },
            "by_language": {}
        }
    
    # ============================================
    # Utility Methods
    # ============================================
    
    def exists(self, news_id: int) -> bool:
        """
        Check if news exists
        
        Args:
            news_id: News ID
            
        Returns:
            True if exists
        """
        return self.db.query(
            self.db.query(News).filter(News.id == news_id).exists()
        ).scalar()
    
    def refresh(self, news: News) -> News:
        """
        Refresh news object from database
        
        Args:
            news: News object to refresh
            
        Returns:
            Refreshed News object
        """
        self.db.refresh(news)
        return news
    
    def close(self):
        """Close database session"""
        self.db.close()
