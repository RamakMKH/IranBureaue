"""
Async News crawler service using Webz.io API
Handles news collection, deduplication, and scoring with async/await
"""
import logging
import asyncio
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz
from sqlalchemy.orm import Session

from app.config import settings
from app.models.news import News, NewsStatus
from app.repositories.news_repository import NewsRepository
from app.utils.proxy import async_proxy_manager
from app.utils.scoring import news_scorer

logger = logging.getLogger(__name__)


class AsyncCrawlerService:
    """
    Async crawler service for Webz.io API
    Uses aiohttp for concurrent HTTP requests
    """
    
    def __init__(self):
        """Initialize async crawler service"""
        self.api_keys = settings.webz_api_keys_list  # Use property method
        self.current_key_index = 0
        self.base_url = "https://api.webz.io/newsApiLite"
        
        logger.info(f"🕷️ Async Crawler initialized with {len(self.api_keys)} API keys")
    
    async def crawl_news(
        self,
        db: Session,
        language: str = "english",
        specific_date: Optional[str] = None,
        max_pages: int = 5,
        limit: int = 100
    ) -> List[News]:
        """
        Crawl news asynchronously
        
        Args:
            db: Database session
            language: News language
            specific_date: Specific date (YYYY-MM-DD)
            max_pages: Maximum pages to fetch
            limit: Maximum results
            
        Returns:
            List of collected news articles
        """
        repo = NewsRepository(db)
        
        # Calculate date range
        if specific_date:
            try:
                start_date = datetime.fromisoformat(specific_date).replace(tzinfo=timezone.utc)
                end_date = start_date + timedelta(days=1)
            except ValueError:
                logger.error(f"❌ Invalid date format: {specific_date}")
                return []
        else:
            start_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1)
        
        # Build query
        query = f"iran category:politics language:{language}"
        timestamp = int(start_date.timestamp() * 1000)
        
        # Build URL
        url = (
            f"{self.base_url}?"
            f"token={self._get_current_token()}&"
            f"q={query}&"
            f"ts={timestamp}&"
            f"highlight=true"
        )
        
        try:
            # Create async session
            session = await async_proxy_manager.create_session(
                timeout=settings.CRAWLER_TIMEOUT
            )
            
            async with session:
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.error(f"❌ Webz.io API error: {response.status}")
                        self._rotate_token()
                        return []
                    
                    data = await response.json()
                    
                    # Log quota
                    if 'requestsLeft' in data:
                        logger.info(f"📊 Webz.io quota: {data['requestsLeft']}")
                    
                    # Process results
                    news_list = await self._process_response(
                        data, language, repo, max_pages, limit, session
                    )
                    
                    logger.info(f"✅ Collected {len(news_list)} articles for {language}")
                    return news_list
                    
        except Exception as e:
            logger.error(f"❌ Crawler error: {e}")
            self._rotate_token()
            return []
    
    async def advanced_crawl(
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
        Advanced async crawl with date range and keywords
        
        Args:
            db: Database session
            date_from: Start date
            date_to: End date
            language: News language
            keywords: Optional keywords
            max_pages: Max pages per day
            limit: Max total results
            
        Returns:
            List of collected news
        """
        repo = NewsRepository(db)
        all_news = []
        current_date = date_from.replace(tzinfo=timezone.utc)
        date_to = date_to.replace(tzinfo=timezone.utc)
        
        # Create session once for all requests
        session = await async_proxy_manager.create_session(
            timeout=settings.CRAWLER_TIMEOUT
        )
        
        async with session:
            while current_date <= date_to and len(all_news) < limit:
                try:
                    # Build query
                    query = self._build_advanced_query(language, keywords)
                    timestamp = int(current_date.timestamp() * 1000)
                    
                    url = (
                        f"{self.base_url}?"
                        f"token={self._get_current_token()}&"
                        f"q={query}&"
                        f"ts={timestamp}&"
                        f"highlight=true"
                    )
                    
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            news_list = await self._process_response(
                                data, language, repo, max_pages,
                                limit - len(all_news), session
                            )
                            all_news.extend(news_list)
                            
                            logger.info(f"📅 {current_date.date()}: {len(news_list)} articles")
                        else:
                            logger.warning(f"⚠️ API error for {current_date.date()}: {response.status}")
                    
                except Exception as e:
                    logger.error(f"❌ Error crawling {current_date.date()}: {e}")
                
                # Move to next day
                current_date += timedelta(days=1)
                await asyncio.sleep(1)  # Rate limiting
        
        logger.info(f"✅ Advanced crawl: {len(all_news)} total articles")
        return all_news
    
    async def _process_response(
        self,
        response_data: dict,
        language: str,
        repo: NewsRepository,
        max_pages: int,
        limit: int,
        session
    ) -> List[News]:
        """Process API response asynchronously"""
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
                    logger.error(f"❌ Error processing post: {e}")
                    continue
            
            # Fetch next page
            if next_url and len(news_list) < limit:
                try:
                    if not next_url.startswith(('http://', 'https://')):
                        next_url = f"https://api.webz.io{next_url}"
                    
                    async with session.get(next_url) as response:
                        response_data = await response.json()
                        next_url = response_data.get('next')
                    
                except Exception as e:
                    logger.error(f"❌ Pagination error: {e}")
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
            published_str = post['published'].replace('Z', '+00:00')
            if '.' in published_str:
                published_str = published_str.split('.')[0] + '+00:00'
            
            try:
                published_date = datetime.fromisoformat(published_str)
            except:
                published_date = datetime.now(timezone.utc)
            
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
                logger.debug(f"⏭️ Duplicate: {post['title'][:50]}")
                return None
            
            # Check minimum score
            if score < 0.3:
                logger.debug(f"⏭️ Low score ({score:.2f}): {post['title'][:50]}")
                return None
            
            # Log high priority
            if score > 0.7:
                logger.info(f"⭐ High score ({score:.2f}): {post['title'][:60]}")
            
            # Create News object
            return News(
                title=post['title'],
                highlight_text=clean_highlight,
                url=post['url'],
                published=published_date,
                domain_rank=post['thread'].get('domain_rank'),
                categories=','.join(categories) if categories else None,
                sentiment=post.get('sentiment'),
                language=language,
                score=score,
                status=NewsStatus.COLLECTED,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            logger.error(f"❌ Error creating news from post: {e}")
            return None
    
    def _is_duplicate(
        self,
        title: str,
        highlight: str,
        recent_news: List[News]
    ) -> bool:
        """Check for duplicates using fuzzy matching"""
        for news in recent_news:
            # Title similarity
            title_similarity = fuzz.ratio(title.lower(), news.title.lower())
            
            if title_similarity > 85:
                return True
            
            # Highlight similarity
            if news.highlight_text and highlight:
                highlight_similarity = fuzz.partial_ratio(
                    highlight.lower()[:200],
                    news.highlight_text.lower()[:200]
                )
                
                if highlight_similarity > 80:
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
        if not self.api_keys:
            logger.error("❌ No API keys configured!")
            return ""
        return self.api_keys[self.current_key_index]
    
    def _rotate_token(self):
        """Rotate to next API token"""
        if not self.api_keys:
            return
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        logger.info(f"🔄 Rotated to API key index: {self.current_key_index}")


# Singleton instance
async_crawler_service = AsyncCrawlerService()