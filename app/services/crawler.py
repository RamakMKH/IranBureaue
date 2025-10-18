"""
News crawler service using Webz.io API
Handles news collection, deduplication, and scoring
"""
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz
from sqlalchemy.orm import Session

from config import settings
from models.news import News, NewsStatus
from repositories.news_repository import NewsRepository
from utils.proxy import proxy_manager
from utils.scoring import news_scorer

logger = logging.getLogger(__name__)


class CrawlerService:
    """Handles news crawling from Webz.io"""
    
    def __init__(self):
        self.api_keys = settings.WEBZ_API_KEYS
        self.current_key_index = 0
        self.base_url = "https://api.webz.io/newsApiLite"
    
    def crawl_news(
        self,
        db: Session,
        language: str = "english",
        specific_date: Optional[str] = None,
        max_pages: int = 5,
        limit: int = 100
    ) -> List[News]:
        """
        Crawl news for a specific language and date
        
        Args:
            db: Database session
            language: News language
            specific_date: Specific date in ISO format (YYYY-MM-DD)
            max_pages: Maximum pages to fetch
            limit: Maximum results to return
            
        Returns:
            List of collected news articles
        """
        repo = NewsRepository(db)
        
        # Calculate date range
        if specific_date:
            try:
                start_date = datetime.fromisoformat(specific_date).replace(tzinfo=timezone.utc)
                end_date = start_date + timedelta(days=1)
            except ValueError as e:
                logger.error(f"Invalid date format: {specific_date}")
                return []
        else:
            start_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1)
        
        # Build query
        query = f"iran category:politics language:{language}"
        timestamp = int(start_date.timestamp() * 1000)
        
        # Make initial request
        url = f"{self.base_url}?token={self._get_current_token()}&q={query}&ts={timestamp}&highlight=true"
        
        try:
            session = proxy_manager.create_session(timeout=settings.CRAWLER_TIMEOUT)
            response = session.get(url, timeout=settings.CRAWLER_TIMEOUT)
            
            if response.status_code != 200:
                logger.error(f"Webz.io API error: {response.status_code}")
                self._rotate_token()
                return []
            
            data = response.json()
            
            # Log quota
            if 'requestsLeft' in data:
                logger.info(f"Webz.io quota remaining: {data['requestsLeft']}")
            
            # Process results
            news_list = self._process_response(data, language, repo, max_pages, limit, session)
            
            logger.info(f"Collected {len(news_list)} news articles for {language}")
            return news_list
            
        except Exception as e:
            logger.error(f"Crawler error: {e}")
            self._rotate_token()
            return []
    
    def advanced_crawl(
        self,
        db: Session,
        date_from: datetime,
        date_to: datetime,
        language: str,
        keywords: Optional[str] = None,
        max_pages: int = 3,
        limit: int = 20
    ) -> List[News]:
        """
        Advanced crawl with custom date range and keywords
        
        Args:
            db: Database session
            date_from: Start date
            date_to: End date
            language: News language
            keywords: Optional keywords (comma-separated)
            max_pages: Maximum pages per day
            limit: Maximum results
            
        Returns:
            List of collected news articles
        """
        repo = NewsRepository(db)
        all_news = []
        current_date = date_from.replace(tzinfo=timezone.utc)
        date_to = date_to.replace(tzinfo=timezone.utc)
        
        while current_date <= date_to and len(all_news) < limit:
            try:
                # Build query with keywords
                query = self._build_advanced_query(language, keywords)
                timestamp = int(current_date.timestamp() * 1000)
                
                url = f"{self.base_url}?token={self._get_current_token()}&q={query}&ts={timestamp}&highlight=true"
                
                session = proxy_manager.create_session(timeout=settings.CRAWLER_TIMEOUT)
                response = session.get(url, timeout=settings.CRAWLER_TIMEOUT)
                
                if response.status_code == 200:
                    data = response.json()
                    news_list = self._process_response(
                        data, language, repo, max_pages, 
                        limit - len(all_news), session
                    )
                    all_news.extend(news_list)
                    
                    logger.info(f"Collected {len(news_list)} news for {current_date.date()}")
                else:
                    logger.warning(f"API error for {current_date.date()}: {response.status_code}")
                
            except Exception as e:
                logger.error(f"Error crawling {current_date.date()}: {e}")
            
            # Move to next day
            current_date += timedelta(days=1)
            time.sleep(1)  # Rate limiting
        
        logger.info(f"Advanced crawl completed: {len(all_news)} total articles")
        return all_news
    
    def _process_response(
        self,
        response_data: dict,
        language: str,
        repo: NewsRepository,
        max_pages: int,
        limit: int,
        session
    ) -> List[News]:
        """Process Webz.io API response"""
        news_list = []
        next_url = response_data.get('next')
        page_count = 0
        
        # Get recent news for duplicate checking
        recent_news = repo.get_recent_for_duplicate_check(days=7)
        
        while next_url and len(news_list) < limit and page_count < max_pages:
            page_count += 1
            
            for post in response_data.get('posts', []):
                if len(news_list) >= limit:
                    break
                
                try:
                    news_article = self._create_news_from_post(post, language, recent_news)
                    
                    if news_article:
                        saved = repo.create(news_article)
                        news_list.append(saved)
                        
                except Exception as e:
                    logger.error(f"Error processing post: {e}")
                    continue
            
            # Fetch next page
            if next_url and len(news_list) < limit:
                try:
                    if not next_url.startswith(('http://', 'https://')):
                        next_url = f"https://api.webz.io{next_url}"
                    
                    response = session.get(next_url, timeout=settings.CRAWLER_TIMEOUT)
                    response_data = response.json()
                    next_url = response_data.get('next')
                    
                except Exception as e:
                    logger.error(f"Pagination error: {e}")
                    break
        
        return news_list
    
    def _create_news_from_post(
        self,
        post: dict,
        language: str,
        recent_news: List[News]
    ) -> Optional[News]:
        """Create News object from API post"""
        try:
            # Parse highlight text
            soup = BeautifulSoup(post['highlightText'], 'html.parser')
            clean_highlight = soup.get_text()
            
            # Parse date
            published_str = post['published'].replace('Z', '')
            published_date = datetime.fromisoformat(published_str)
            
            # Calculate score
            categories = post.get('categories', [])
            score = news_scorer.calculate_total_score(
                published_date=published_date,
                title=post['title'],
                highlight_text=clean_highlight,
                domain_rank=post['thread'].get('domain_rank', 500000),
                categories=categories
            )
            
            # Check for duplicates
            if self._is_duplicate(post['title'], clean_highlight, recent_news):
                logger.debug(f"Skipping duplicate: {post['title'][:50]}")
                return None
            
            # Check minimum score threshold
            if score < 0.3:
                logger.debug(f"Skipping low score ({score}): {post['title'][:50]}")
                return None
            
            # Log high priority news
            if news_scorer.is_high_priority(score):
                logger.info(f"High priority news (score: {score}): {post['title']}")
            
            # Create News object
            return News(
                title=post['title'],
                highlight_text=clean_highlight,
                published=published_date,
                domain_rank=post['thread'].get('domain_rank'),
                categories=','.join(categories),
                sentiment=post.get('sentiment', ''),
                language=language,
                url=post['url'],
                score=score,
                status=NewsStatus.COLLECTED
            )
            
        except Exception as e:
            logger.error(f"Error creating news from post: {e}")
            return None
    
    def _is_duplicate(self, title: str, highlight: str, recent_news: List[News]) -> bool:
        """Check if news is duplicate using fuzzy matching"""
        combined_text = f"{title} {highlight}"
        
        for existing in recent_news:
            existing_text = f"{existing.title} {existing.highlight_text}"
            similarity = fuzz.ratio(combined_text, existing_text)
            
            if similarity > 80:
                return True
        
        return False
    
    def _build_advanced_query(self, language: str, keywords: Optional[str]) -> str:
        """Build advanced search query"""
        base_query = "iran"
        lang_filter = f" language:{language}"
        
        if keywords and keywords.strip():
            keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
            if keyword_list:
                keyword_query = " OR ".join(keyword_list)
                return f"({base_query}) AND ({keyword_query}){lang_filter}"
        
        return f"{base_query}{lang_filter}"
    
    def _get_current_token(self) -> str:
        """Get current API token"""
        return self.api_keys[self.current_key_index]
    
    def _rotate_token(self):
        """Rotate to next API token"""
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        logger.info(f"Rotated to API key index: {self.current_key_index}")


# Singleton instance
crawler_service = CrawlerService()