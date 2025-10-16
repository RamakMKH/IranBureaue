"""
Proxy management utilities
Handles SOCKS5 proxy configuration for HTTP requests
"""
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional
from config import settings

logger = logging.getLogger(__name__)


class ProxyManager:
    """
    Manages proxy configuration for HTTP requests
    Provides configured requests sessions with proxy support
    """
    
    def __init__(self):
        """Initialize proxy manager"""
        self.proxy_enabled = bool(settings.SOCKS5_PROXY)
        self.proxy_config = self._parse_proxy() if self.proxy_enabled else None
        
        if self.proxy_enabled:
            logger.info(
                f"🔧 Proxy enabled: "
                f"{self.proxy_config['host']}:{self.proxy_config['port']}"
            )
        else:
            logger.info("🔧 Proxy disabled: Direct connections")
    
    def _parse_proxy(self) -> Optional[dict]:
        """
        Parse proxy configuration from settings
        
        Returns:
            Dictionary with proxy configuration or None
        """
        try:
            proxy_url = settings.SOCKS5_PROXY
            
            # Remove socks5:// prefix if present
            proxy_url = proxy_url.replace('socks5://', '')
            proxy_url = proxy_url.replace('socks5h://', '')
            
            # Parse host and port
            if ':' in proxy_url:
                parts = proxy_url.split(':')
                host = parts[0]
                port = int(parts[1])
            else:
                host = proxy_url
                port = 1080  # Default SOCKS5 port
            
            return {
                'host': host,
                'port': port,
                'url': f'socks5://{host}:{port}'
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to parse proxy configuration: {e}")
            return None
    
    def create_session(
        self, 
        timeout: int = 30, 
        max_retries: int = 3,
        backoff_factor: float = 1.0
    ) -> requests.Session:
        """
        Create a requests session with proxy and retry configuration
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
            backoff_factor: Backoff factor between retries
            
        Returns:
            Configured requests.Session object
        """
        session = requests.Session()
        
        # Configure proxy if enabled
        if self.proxy_enabled and self.proxy_config:
            try:
                proxy_url = self.proxy_config['url']
                session.proxies = {
                    'http': proxy_url,
                    'https': proxy_url
                }
                logger.debug(
                    f"🔧 Session configured with proxy: "
                    f"{self.proxy_config['host']}:{self.proxy_config['port']}"
                )
            except Exception as e:
                logger.warning(f"⚠️ Failed to configure proxy: {e}")
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]
        )
        
        # Add retry adapter
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount('https://', adapter)
        session.mount('http://', adapter)
        
        # Set default timeout
        session.timeout = timeout
        
        return session
    
    def test_connection(
        self, 
        test_url: str = "https://api.telegram.org",
        timeout: int = 10
    ) -> bool:
        """
        Test proxy connection
        
        Args:
            test_url: URL to test connection against
            timeout: Request timeout in seconds
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            session = self.create_session(timeout=timeout, max_retries=1)
            response = session.get(test_url, timeout=timeout)
            
            if response.status_code == 200:
                logger.info("✅ Proxy connection test successful")
                return True
            else:
                logger.warning(
                    f"⚠️ Proxy connection test returned status: {response.status_code}"
                )
                return False
                
        except Exception as e:
            logger.error(f"❌ Proxy connection test failed: {e}")
            return False
    
    def get_session_with_custom_headers(
        self,
        headers: dict,
        timeout: int = 30,
        max_retries: int = 3
    ) -> requests.Session:
        """
        Create session with custom headers
        
        Args:
            headers: Dictionary of custom headers
            timeout: Request timeout
            max_retries: Maximum retries
            
        Returns:
            Configured session with custom headers
        """
        session = self.create_session(timeout=timeout, max_retries=max_retries)
        session.headers.update(headers)
        
        logger.debug(f"🔧 Session created with custom headers: {list(headers.keys())}")
        return session
    
    def get_status(self) -> dict:
        """
        Get proxy manager status
        
        Returns:
            Dictionary with proxy status information
        """
        status = {
            "enabled": self.proxy_enabled,
            "configured": self.proxy_config is not None
        }
        
        if self.proxy_config:
            status.update({
                "host": self.proxy_config['host'],
                "port": self.proxy_config['port'],
                "url": self.proxy_config['url']
            })
        
        return status
    
    def test_multiple_urls(
        self, 
        urls: list,
        timeout: int = 10
    ) -> dict:
        """
        Test connection to multiple URLs
        
        Args:
            urls: List of URLs to test
            timeout: Request timeout
            
        Returns:
            Dictionary with test results for each URL
        """
        results = {}
        
        for url in urls:
            try:
                session = self.create_session(timeout=timeout, max_retries=1)
                response = session.get(url, timeout=timeout)
                
                results[url] = {
                    "success": response.status_code == 200,
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds()
                }
                
                logger.debug(
                    f"🔍 {url}: "
                    f"{'✅' if results[url]['success'] else '❌'} "
                    f"({response.status_code})"
                )
                
            except Exception as e:
                results[url] = {
                    "success": False,
                    "error": str(e)
                }
                logger.error(f"❌ {url}: {e}")
        
        return results
    
    def get_external_ip(self) -> Optional[str]:
        """
        Get external IP address (useful for verifying proxy)
        
        Returns:
            External IP address or None if failed
        """
        try:
            session = self.create_session(timeout=10, max_retries=1)
            response = session.get('https://api.ipify.org?format=json', timeout=10)
            
            if response.status_code == 200:
                ip = response.json().get('ip')
                logger.info(f"🌐 External IP: {ip}")
                return ip
            else:
                logger.warning(f"⚠️ Failed to get external IP: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error getting external IP: {e}")
            return None
    
    def verify_proxy_working(self) -> bool:
        """
        Verify that proxy is actually being used
        Compares direct vs proxied connections
        
        Returns:
            True if proxy appears to be working
        """
        if not self.proxy_enabled:
            logger.info("ℹ️ Proxy not enabled, skipping verification")
            return True
        
        try:
            # Get IP with proxy
            proxied_ip = self.get_external_ip()
            
            if proxied_ip:
                logger.info(f"✅ Proxy verification: Using IP {proxied_ip}")
                return True
            else:
                logger.warning("⚠️ Could not verify proxy IP")
                return False
                
        except Exception as e:
            logger.error(f"❌ Proxy verification failed: {e}")
            return False


# Singleton instance
proxy_manager = ProxyManager()


# Utility functions
def get_session(timeout: int = 30, max_retries: int = 3) -> requests.Session:
    """
    Convenience function to get a configured session
    
    Args:
        timeout: Request timeout
        max_retries: Maximum retries
        
    Returns:
        Configured requests.Session
    """
    return proxy_manager.create_session(timeout=timeout, max_retries=max_retries)


def test_proxy() -> bool:
    """
    Convenience function to test proxy
    
    Returns:
        True if proxy test successful
    """
    return proxy_manager.test_connection()


def get_proxy_status() -> dict:
    """
    Convenience function to get proxy status
    
    Returns:
        Dictionary with proxy status
    """
    return proxy_manager.get_status()
