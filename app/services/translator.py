"""
Translation service using Gemini AI and Google Translate
"""
import logging
import time
from typing import Optional
from deep_translator import GoogleTranslator
from app.config import settings
from app.utils.proxy import proxy_manager

logger = logging.getLogger(__name__)


class TranslationService:
    """Handles news translation with multiple providers"""
    
    def __init__(self):
        self.gemini_keys = settings.GEMINI_API_KEYS
        self.current_gemini_key = 0
        self.max_retries = 3
    
    def translate(self, text: str, target_lang: str = 'fa') -> Optional[str]:
        """
        Translate text with fallback mechanism
        
        Args:
            text: Text to translate
            target_lang: Target language code
            
        Returns:
            Translated text or None on failure
        """
        if not text or len(text.strip()) == 0:
            return ""
        
        # Truncate if too long
        if len(text) > settings.MAX_TRANSLATION_LENGTH:
            logger.warning(f"Text too long ({len(text)} chars), truncating...")
            text = text[:settings.MAX_TRANSLATION_LENGTH]
        
        # Try Gemini AI first
        if self.gemini_keys and self.gemini_keys[0]:
            gemini_result = self._translate_with_gemini(text, target_lang)
            if gemini_result:
                return gemini_result
        
        # Fallback to Google Translate
        logger.info("Falling back to Google Translate")
        return self._translate_with_google(text, target_lang)
    
    def _translate_with_gemini(self, text: str, target_lang: str) -> Optional[str]:
        """
        Translate using Gemini AI
        
        Args:
            text: Text to translate
            target_lang: Target language
            
        Returns:
            Translated text or None
        """
        for attempt in range(self.max_retries):
            try:
                # Prepare prompt
                prompt = self._create_gemini_prompt(text, target_lang)
                
                # API configuration
                url = "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent"
                params = {"key": self.gemini_keys[self.current_gemini_key]}
                
                payload = {
                    "contents": [{
                        "parts": [{"text": prompt}]
                    }],
                    "generationConfig": {
                        "temperature": 0.3,
                        "topP": 0.8,
                        "maxOutputTokens": 1024
                    }
                }
                
                # Make request with proxy
                session = proxy_manager.create_session(timeout=settings.TRANSLATION_TIMEOUT)
                response = session.post(url, params=params, json=payload, timeout=settings.TRANSLATION_TIMEOUT)
                
                if response.status_code == 200:
                    data = response.json()
                    translated_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    
                    # Clean up formatting
                    translated_text = self._clean_translation(translated_text)
                    
                    logger.info(f"Gemini translation successful: {len(text)} -> {len(translated_text)} chars")
                    return translated_text
                else:
                    logger.warning(f"Gemini API returned status {response.status_code}")
                    raise Exception(f"API error: {response.status_code}")
                    
            except Exception as e:
                logger.warning(f"Gemini translation attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    # Rotate API key
                    self.current_gemini_key = (self.current_gemini_key + 1) % len(self.gemini_keys)
                    logger.info(f"Rotated to Gemini key index: {self.current_gemini_key}")
                    time.sleep(2)
        
        return None
    
    def _translate_with_google(self, text: str, target_lang: str) -> Optional[str]:
        """
        Translate using Google Translate
        
        Args:
            text: Text to translate
            target_lang: Target language
            
        Returns:
            Translated text or None
        """
        try:
            translator = GoogleTranslator(source='auto', target=target_lang)
            translated = translator.translate(text)
            
            # Apply improvements
            improved = self._improve_translation(translated)
            
            logger.info(f"Google translation successful: {len(text)} -> {len(improved)} chars")
            return improved
            
        except Exception as e:
            logger.error(f"Google translation failed: {e}")
            return None
    
    def _create_gemini_prompt(self, text: str, target_lang: str) -> str:
        """Create prompt for Gemini AI translation"""
        if target_lang == 'fa':
            return f"""
You are a professional international political news translator. Translate and summarize the news text below into fluent and natural Persian.

Important instructions:
1. The translation must be completely fluent, smooth and understandable for Persian speakers
2. Accurately convey political and international terms
3. Optimize sentence structure for easy reading
4. Avoid literal word-for-word translation
5. Final text should be 150-200 words maximum (intelligent summarization)
6. Focus on main and key points of the news
7. The result must be standalone and the reader should understand the whole subject by reading it

News text for translation and summarization:
{text}

Return only the final fluent and summarized translation.
"""
        return f"Translate the following text to {target_lang}: {text}"
    
    def _clean_translation(self, text: str) -> str:
        """Clean translated text"""
        # Remove markdown formatting
        text = text.replace('**', '').replace('*', '')
        
        # Remove unwanted phrases
        unwanted_phrases = ["Translation:", "Summary:", "Translated text:"]
        for phrase in unwanted_phrases:
            text = text.replace(phrase, "")
        
        return text.strip()
    
    def _improve_translation(self, text: str) -> str:
        """Improve Google Translate quality"""
        if not text or len(text.strip()) < 10:
            return text
        
        try:
            # Common Persian corrections
            corrections = {
                "طرفین": "طرفین",
                "طرف ها": "طرف‌ها",
                "سلاح های": "سلاح‌های",
                "تحریم های": "تحریم‌های",
                "قطعنامه های": "قطعنامه‌های",
                "نیروهای امنیتی": "نیروهای امنیتی",
                "روابط دو جانبه": "روابط دوجانبه",
                "همکاری های": "همکاری‌های",
                "مذاکرات صلح": "مذاکرات صلح",
                "شورای امنیت": "شورای امنیت",
                "رئیس جمهور": "رئیس‌جمهور",
                "وزیر امور خارجه": "وزیر امور خارجه",
                "برجام": "برجام",
                "تحریم هسته ای": "تحریم هسته‌ای",
                "اظهار داشت": "گفت",
                "عنوان کرد": "گفت",
                "خاطرنشان کرد": "گفت",
                "میباشد": "است",
                "می‌باشد": "است",
                "نمود": "کرد",
            }
            
            for wrong, correct in corrections.items():
                text = text.replace(wrong, correct)
            
            # Fix punctuation spacing
            text = text.replace(" .", ".")
            text = text.replace(" ,", ",")
            text = text.replace(" :", ":")
            
            # Remove extra spaces
            text = ' '.join(text.split())
            
            return text
            
        except Exception as e:
            logger.error(f"Translation improvement error: {e}")
            return text


# Singleton instance
translation_service = TranslationService()