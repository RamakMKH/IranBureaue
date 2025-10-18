"""
Telegram service for publishing news
"""
import logging
import random
from typing import Optional
from config import settings
from utils.proxy import proxy_manager
from models.news import News

logger = logging.getLogger(__name__)


class TelegramService:
    """Handles Telegram message publishing"""
    
    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.channel_id = settings.TELEGRAM_CHANNEL
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    def send_message(self, message: str, disable_preview: bool = False) -> bool:
        """
        Send message to Telegram channel
        
        Args:
            message: Message text (HTML formatted)
            disable_preview: Disable web page preview
            
        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.channel_id,
                'text': message,
                'disable_web_page_preview': disable_preview,
                'parse_mode': 'HTML'
            }
            
            session = proxy_manager.create_session(timeout=30)
            response = session.post(url, json=payload, timeout=30)
            
            if response.status_code == 200:
                logger.info("Message sent to Telegram successfully")
                return True
            else:
                logger.error(f"Telegram API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
    
    def create_news_message(self, news: News) -> str:
        """
        Create formatted message for news article
        
        Args:
            news: News article
            
        Returns:
            Formatted HTML message
        """
        # Title variations
        title_variants = [
            news.title,
            f"📰 {news.title}",
            f"خبر فوری: {news.title}",
            f"🔴 {news.title}"
        ]
        
        # Hashtags
        hashtag_variants = [
            "#خبر #ایران #سیاسی",
            "#ایران #سیاسی #بین_المللی",
            "#خبر_فوری #ایران #سیاسی",
            "#تحلیل_سیاسی #ایران #خارجی"
        ]
        
        # Use edited text if available, otherwise translated summary
        content = news.edited_text or news.translated_summary
        
        if content:
            # Clean and optimize content
            content = self._clean_content(content)
        else:
            content = "متن ترجمه شده در دسترس نیست."
        
        # Build message
        message = f"""
{random.choice(title_variants)}

{content}

📖 ادامه مطلب: {news.url}

{random.choice(hashtag_variants)}
🔹 @IranBureau
        """
        
        return message.strip()
    
    def _clean_content(self, content: str) -> str:
        """
        Clean and optimize content for Telegram
        
        Args:
            content: Raw content
            
        Returns:
            Cleaned content
        """
        # Split into sentences
        sentences = content.split('.')
        unique_sentences = []
        seen = set()
        
        for sentence in sentences:
            clean = sentence.strip()
            
            # Skip short, duplicate, or unwanted sentences
            if (clean and 
                len(clean) > 10 and 
                clean not in seen and
                not clean.startswith('این متن را') and
                not clean.startswith('ویرایش کنید')):
                
                unique_sentences.append(clean)
                seen.add(clean)
        
        # Limit to 3-4 sentences
        final_content = '. '.join(unique_sentences[:4]) + '.'
        
        # Truncate if too long
        if len(final_content) > 600:
            final_content = final_content[:600] + "..."
        
        return final_content
    
    def test_connection(self) -> bool:
        """
        Test Telegram connection
        
        Returns:
            True if connection successful
        """
        try:
            url = f"{self.base_url}/getMe"
            session = proxy_manager.create_session(timeout=10)
            response = session.get(url, timeout=10)
            
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Telegram connection test failed: {e}")
            return False
    
    def send_test_message(self) -> bool:
        """Send a test message to verify configuration"""
        test_message = "🔧 Test connection: If you see this message, Telegram connection is working."
        return self.send_message(test_message)


# Singleton instance
telegram_service = TelegramService()