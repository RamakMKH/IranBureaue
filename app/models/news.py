"""
Database models for News System
SQLAlchemy ORM models with proper indexes and relationships
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class NewsStatus:
    """News status constants"""
    COLLECTED = "collected"
    APPROVED_FOR_TRANSLATE = "approved_for_translate"
    TRANSLATED_EDITED = "translated_edited"
    READY_FOR_FINAL = "ready_for_final"
    PUBLISHED_QUEUE = "published_queue"
    PUBLISHED = "published"
    
    @classmethod
    def all_statuses(cls):
        """Get all available statuses"""
        return [
            cls.COLLECTED,
            cls.APPROVED_FOR_TRANSLATE,
            cls.TRANSLATED_EDITED,
            cls.READY_FOR_FINAL,
            cls.PUBLISHED_QUEUE,
            cls.PUBLISHED
        ]


class News(Base):
    """
    News article model
    Represents a news article with all its metadata
    """
    __tablename__ = 'news'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Content fields
    title = Column(String(500), nullable=False, index=True)
    highlight_text = Column(Text)
    url = Column(String(500), unique=True, nullable=False)
    
    # Metadata
    published = Column(DateTime, nullable=False, index=True)
    domain_rank = Column(Integer)
    categories = Column(String(300))  # Comma-separated categories
    sentiment = Column(String(50))
    language = Column(String(50), nullable=False, index=True)
    
    # Scoring and workflow
    score = Column(Float, default=0.0, index=True)
    status = Column(String(50), default=NewsStatus.COLLECTED, index=True)
    
    # Translation fields
    translated_summary = Column(Text)
    edited_text = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Composite indexes for better query performance
    __table_args__ = (
        Index('idx_status_score', 'status', 'score'),
        Index('idx_language_status', 'language', 'status'),
        Index('idx_published_status', 'published', 'status'),
        Index('idx_created_status', 'created_at', 'status'),
    )
    
    def __repr__(self):
        """String representation"""
        return f"<News(id={self.id}, title='{self.title[:50]}...', status='{self.status}')>"
    
    def to_dict(self):
        """
        Convert model to dictionary
        Useful for JSON serialization
        """
        return {
            'id': self.id,
            'title': self.title,
            'highlight_text': self.highlight_text,
            'url': self.url,
            'published': self.published.isoformat() if self.published else None,
            'domain_rank': self.domain_rank,
            'categories': self.categories,
            'sentiment': self.sentiment,
            'language': self.language,
            'score': self.score,
            'status': self.status,
            'translated_summary': self.translated_summary,
            'edited_text': self.edited_text,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @property
    def is_translated(self):
        """Check if news has been translated"""
        return bool(self.translated_summary)
    
    @property
    def is_ready_for_publish(self):
        """Check if news is ready for publishing"""
        return self.status in [NewsStatus.PUBLISHED_QUEUE, NewsStatus.READY_FOR_FINAL]
    
    @property
    def is_published(self):
        """Check if news has been published"""
        return self.status == NewsStatus.PUBLISHED
    
    @property
    def categories_list(self):
        """Get categories as list"""
        if not self.categories:
            return []
        return [cat.strip() for cat in self.categories.split(',')]
    
    def get_display_text(self):
        """
        Get the best available text for display
        Priority: edited_text > translated_summary > highlight_text
        """
        if self.edited_text:
            return self.edited_text
        elif self.translated_summary:
            return self.translated_summary
        else:
            return self.highlight_text