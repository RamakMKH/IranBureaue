"""
News scoring algorithm
Calculate relevance and priority scores for news articles
Uses multiple factors: urgency, relevance, credibility, diversity
"""
import logging
from datetime import datetime, timezone
from typing import List, Optional

logger = logging.getLogger(__name__)


class NewsScorer:
    """
    Calculate scores for news articles based on multiple factors
    Higher score = Higher priority
    """
    
    # Scoring weights (must sum to 1.0)
    WEIGHTS = {
        'urgency': 0.30,      # How recent is the news
        'relevance': 0.30,    # How relevant to Iran
        'credibility': 0.20,  # Source credibility (domain rank)
        'diversity': 0.20     # Content diversity (categories)
    }
    
    # Default high-priority keywords
    DEFAULT_KEYWORDS = [
        'iran', 'iranian', 'tehran', 'persia', 'persian',
        'nuclear', 'sanctions', 'jcpoa', 'irgc',
        'khamenei', 'raisi', 'president', 'supreme leader'
    ]
    
    # High-value categories
    HIGH_VALUE_CATEGORIES = [
        'Politics',
        'Economy, Business and Finance',
        'International Relations',
        'Security',
        'Defense',
        'Diplomacy'
    ]
    
    @staticmethod
    def calculate_urgency(published_date: datetime) -> float:
        """
        Calculate urgency score based on publication date
        Newer articles get higher scores
        
        Args:
            published_date: Publication datetime
            
        Returns:
            Urgency score (0.0 - 1.0)
        """
        try:
            now = datetime.now(timezone.utc)
            
            # Make published_date timezone-aware if it isn't
            if published_date.tzinfo is None:
                published_date = published_date.replace(tzinfo=timezone.utc)
            
            # Calculate age in days
            age_seconds = (now - published_date).total_seconds()
            age_days = age_seconds / 86400  # 86400 seconds in a day
            
            # Score decreases linearly over 30 days
            # Day 0: 1.0, Day 30: 0.0
            if age_days < 0:
                # Future date? Give it max score
                urgency = 1.0
            elif age_days <= 30:
                urgency = max(0, 1.0 - (age_days / 30.0))
            else:
                # Older than 30 days gets minimum score
                urgency = 0.0
            
            logger.debug(f"⏰ Urgency: {urgency:.3f} (age: {age_days:.1f} days)")
            return urgency
            
        except Exception as e:
            logger.error(f"❌ Error calculating urgency: {e}")
            return 0.5  # Default middle score
    
    @staticmethod
    def calculate_relevance(
        text: str, 
        keywords: Optional[List[str]] = None
    ) -> float:
        """
        Calculate relevance score based on keyword presence
        
        Args:
            text: Article text (title + highlight)
            keywords: List of relevant keywords (optional)
            
        Returns:
            Relevance score (0.0 - 1.0)
        """
        if not text:
            return 0.0
        
        text_lower = text.lower()
        
        # Use provided keywords or default
        if keywords is None:
            keywords = NewsScorer.DEFAULT_KEYWORDS
        
        # Count keyword matches
        matches = sum(1 for keyword in keywords if keyword.lower() in text_lower)
        
        if matches == 0:
            # No keywords found
            relevance = 0.3  # Base score
        elif matches == 1:
            relevance = 0.6
        elif matches == 2:
            relevance = 0.8
        else:
            # 3+ keywords
            relevance = 1.0
        
        logger.debug(f"🔍 Relevance: {relevance:.3f} ({matches} keywords matched)")
        return relevance
    
    @staticmethod
    def calculate_credibility(domain_rank: Optional[int]) -> float:
        """
        Calculate credibility score based on domain rank
        Lower rank number = More credible = Higher score
        
        Args:
            domain_rank: Domain ranking (lower is better)
            
        Returns:
            Credibility score (0.0 - 1.0)
        """
        if not domain_rank or domain_rank <= 0:
            # Unknown domain rank
            return 0.5  # Middle score
        
        # Normalize domain rank
        # Rank 1-1000: Very credible (0.9-1.0)
        # Rank 1000-10000: Credible (0.7-0.9)
        # Rank 10000-100000: Medium (0.4-0.7)
        # Rank 100000-1000000: Low (0.1-0.4)
        # Rank >1000000: Very low (0.0-0.1)
        
        if domain_rank <= 1000:
            credibility = 0.9 + (0.1 * (1000 - domain_rank) / 1000)
        elif domain_rank <= 10000:
            credibility = 0.7 + (0.2 * (10000 - domain_rank) / 9000)
        elif domain_rank <= 100000:
            credibility = 0.4 + (0.3 * (100000 - domain_rank) / 90000)
        elif domain_rank <= 1000000:
            credibility = 0.1 + (0.3 * (1000000 - domain_rank) / 900000)
        else:
            credibility = 0.1 * (2000000 - domain_rank) / 1000000
            credibility = max(0.0, credibility)
        
        logger.debug(f"🏆 Credibility: {credibility:.3f} (rank: {domain_rank})")
        return credibility
    
    @staticmethod
    def calculate_diversity(categories: List[str]) -> float:
        """
        Calculate diversity score based on article categories
        High-value categories get higher scores
        
        Args:
            categories: List of article categories
            
        Returns:
            Diversity score (0.0 - 1.0)
        """
        if not categories:
            return 0.5  # Default middle score
        
        # Check for high-value categories
        high_value_count = sum(
            1 for cat in categories 
            if cat in NewsScorer.HIGH_VALUE_CATEGORIES
        )
        
        if high_value_count == 0:
            diversity = 0.4
        elif high_value_count == 1:
            diversity = 0.7
        else:
            # Multiple high-value categories
            diversity = 1.0
        
        logger.debug(
            f"🎯 Diversity: {diversity:.3f} "
            f"({high_value_count} high-value categories)"
        )
        return diversity
    
    @classmethod
    def calculate_total_score(
        cls,
        published_date: datetime,
        title: str,
        highlight_text: str,
        domain_rank: Optional[int],
        categories: List[str],
        keywords: Optional[List[str]] = None,
        custom_weights: Optional[dict] = None
    ) -> float:
        """
        Calculate total score for a news article
        Combines all scoring factors with weights
        
        Args:
            published_date: Publication datetime
            title: Article title
            highlight_text: Article highlight/summary
            domain_rank: Domain ranking
            categories: List of categories
            keywords: Optional custom keywords
            custom_weights: Optional custom weights (overrides defaults)
            
        Returns:
            Total score (0.0 - 1.0)
        """
        # Combine title and text for analysis
        full_text = f"{title} {highlight_text}"
        
        # Calculate individual scores
        urgency = cls.calculate_urgency(published_date)
        relevance = cls.calculate_relevance(full_text, keywords)
        credibility = cls.calculate_credibility(domain_rank)
        diversity = cls.calculate_diversity(categories)
        
        # Use custom weights if provided, otherwise use defaults
        weights = custom_weights if custom_weights else cls.WEIGHTS
        
        # Calculate weighted average
        total_score = (
            urgency * weights['urgency'] +
            relevance * weights['relevance'] +
            credibility * weights['credibility'] +
            diversity * weights['diversity']
        )
        
        # Round to 3 decimal places
        total_score = round(total_score, 3)
        
        logger.info(
            f"📊 Total Score: {total_score:.3f} "
            f"[U:{urgency:.2f} R:{relevance:.2f} "
            f"C:{credibility:.2f} D:{diversity:.2f}]"
        )
        
        return total_score
    
    @classmethod
    def is_high_priority(cls, score: float, threshold: float = 0.7) -> bool:
        """
        Check if news is high priority based on score
        
        Args:
            score: News score
            threshold: Priority threshold (default: 0.7)
            
        Returns:
            True if high priority
        """
        return score >= threshold
    
    @classmethod
    def get_priority_level(cls, score: float) -> str:
        """
        Get priority level description based on score
        
        Args:
            score: News score
            
        Returns:
            Priority level string
        """
        if score >= 0.9:
            return "critical"
        elif score >= 0.7:
            return "high"
        elif score >= 0.5:
            return "medium"
        elif score >= 0.3:
            return "low"
        else:
            return "very_low"
    
    @classmethod
    def batch_score(
        cls,
        articles: List[dict]
    ) -> List[dict]:
        """
        Score multiple articles at once
        
        Args:
            articles: List of article dictionaries with required fields
            
        Returns:
            List of articles with added 'score' field
        """
        scored_articles = []
        
        for article in articles:
            try:
                score = cls.calculate_total_score(
                    published_date=article['published_date'],
                    title=article['title'],
                    highlight_text=article.get('highlight_text', ''),
                    domain_rank=article.get('domain_rank'),
                    categories=article.get('categories', []),
                    keywords=article.get('keywords')
                )
                
                article['score'] = score
                article['priority_level'] = cls.get_priority_level(score)
                scored_articles.append(article)
                
            except Exception as e:
                logger.error(f"❌ Error scoring article: {e}")
                article['score'] = 0.0
                article['priority_level'] = 'error'
                scored_articles.append(article)
        
        # Sort by score (highest first)
        scored_articles.sort(key=lambda x: x['score'], reverse=True)
        
        logger.info(f"📊 Batch scored {len(scored_articles)} articles")
        return scored_articles
    
    @classmethod
    def explain_score(
        cls,
        published_date: datetime,
        title: str,
        highlight_text: str,
        domain_rank: Optional[int],
        categories: List[str]
    ) -> dict:
        """
        Get detailed explanation of score calculation
        Useful for debugging and transparency
        
        Args:
            (same as calculate_total_score)
            
        Returns:
            Dictionary with detailed scoring breakdown
        """
        full_text = f"{title} {highlight_text}"
        
        urgency = cls.calculate_urgency(published_date)
        relevance = cls.calculate_relevance(full_text)
        credibility = cls.calculate_credibility(domain_rank)
        diversity = cls.calculate_diversity(categories)
        
        total = cls.calculate_total_score(
            published_date, title, highlight_text,
            domain_rank, categories
        )
        
        return {
            "total_score": total,
            "priority_level": cls.get_priority_level(total),
            "components": {
                "urgency": {
                    "score": urgency,
                    "weight": cls.WEIGHTS['urgency'],
                    "contribution": urgency * cls.WEIGHTS['urgency']
                },
                "relevance": {
                    "score": relevance,
                    "weight": cls.WEIGHTS['relevance'],
                    "contribution": relevance * cls.WEIGHTS['relevance']
                },
                "credibility": {
                    "score": credibility,
                    "weight": cls.WEIGHTS['credibility'],
                    "contribution": credibility * cls.WEIGHTS['credibility']
                },
                "diversity": {
                    "score": diversity,
                    "weight": cls.WEIGHTS['diversity'],
                    "contribution": diversity * cls.WEIGHTS['diversity']
                }
            },
            "metadata": {
                "domain_rank": domain_rank,
                "categories": categories,
                "published_date": published_date.isoformat()
            }
        }


# Singleton instance
news_scorer = NewsScorer()


# Convenience functions
def score_news(
    published_date: datetime,
    title: str,
    highlight_text: str,
    domain_rank: Optional[int],
    categories: List[str]
) -> float:
    """
    Convenience function to score a news article
    
    Returns:
        Score (0.0 - 1.0)
    """
    return news_scorer.calculate_total_score(
        published_date, title, highlight_text,
        domain_rank, categories
    )


def is_high_priority(score: float) -> bool:
    """
    Convenience function to check if score is high priority
    
    Returns:
        True if high priority
    """
    return news_scorer.is_high_priority(score)
