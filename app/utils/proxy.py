"""
Async Proxy management utilities
Handles SOCKS5 proxy configuration for HTTP requests using aiohttp
"""
import logging
import aiohttp
from aiohttp_socks import ProxyConnector
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)


class AsyncProxyManager:
    """
    Manages async proxy configuration for HTTP requests
    Provides configured aiohttp sessions with SOCKS5 proxy support
    """
    
    def __init__(self):
        """Initialize async proxy manager"""
        self.proxy_enabled = bool(settings.SOCKS5_PROXY)
        self.proxy_url = settings.SOCKS5_PROXY if self.proxy_enabled else None
        
        if self.proxy_enabled:
            logger.info(f"🔧 Async Proxy enabled: {self.proxy_url}")
        else:
            logger.info("🔧 Async Proxy disabled: Direct connections")
    
    def create_connector(self, timeout: int = 30) -> Optional[ProxyConnector]:
        """
        Create aiohttp ProxyConnector for SOCKS5
        
        Args:
            timeout: Connection timeout in seconds
            
        Returns:
            ProxyConnector or None
        """
        if not self.proxy_enabled or not self.proxy_url:
            return None
        
        try:
            # aiohttp-socks handles socks5:// URLs directly
            connector = ProxyConnector.from_url(self.proxy_url)
            logger.debug(f"🔧 Connector created with proxy: {self.proxy_url}")
            return connector
        except Exception as e:
            logger.error(f"❌ Failed to create proxy connector: {e}")
            return None
    
    async def create_session(
        self, 
        timeout: int = 30,
        headers: Optional[dict] = None
    ) -> aiohttp.ClientSession:
        """
        Create an async aiohttp session with proxy support
        
        Args:
            timeout: Request timeout in seconds
            headers: Optional custom headers
            
        Returns:
            Configured aiohttp.ClientSession
        """
        # Create connector (with or without proxy)
        connector = self.create_connector(timeout=timeout)
        
        # Create timeout config
        timeout_config = aiohttp.ClientTimeout(total=timeout)
        
        # Create session
        session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout_config,
            headers=headers or {}
        )
        
        logger.debug(f"🔧 Async session created (proxy: {self.proxy_enabled})")
        return session
    
    async def test_connection(
        self, 
        test_url: str = "https://api.ipify.org?format=json",
        timeout: int = 10
    ) -> bool:
        """
        Test proxy connection asynchronously
        
        Args:
            test_url: URL to test connection against
            timeout: Request timeout in seconds
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            session = await self.create_session(timeout=timeout)
            
            async with session:
                async with session.get(test_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        ip = data.get('ip', 'unknown')
                        logger.info(f"✅ Proxy test successful - IP: {ip}")
                        return True
                    else:
                        logger.warning(f"⚠️ Proxy test returned status: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ Proxy connection test failed: {e}")
            return False
    
    async def get_external_ip(self) -> Optional[str]:
        """
        Get external IP address asynchronously
        
        Returns:
            External IP address or None if failed
        """
        try:
            session = await self.create_session(timeout=10)
            
            async with session:
                async with session.get('https://api.ipify.org?format=json') as response:
                    if response.status == 200:
                        data = await response.json()
                        ip = data.get('ip')
                        logger.info(f"🌐 External IP: {ip}")
                        return ip
                    else:
                        logger.warning(f"⚠️ Failed to get IP: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"❌ Error getting external IP: {e}")
            return None
    
    def get_status(self) -> dict:
        """
        Get proxy manager status
        
        Returns:
            Dictionary with proxy status information
        """
        return {
            "enabled": self.proxy_enabled,
            "proxy_url": self.proxy_url if self.proxy_enabled else None,
            "type": "aiohttp + aiohttp-socks"
        }


# Singleton instance
async_proxy_manager = AsyncProxyManager()


# Utility functions
async def get_session(timeout: int = 30, headers: Optional[dict] = None) -> aiohttp.ClientSession:
    """
    Convenience function to get a configured async session
    
    Args:
        timeout: Request timeout
        headers: Optional custom headers
        
    Returns:
        Configured aiohttp.ClientSession
    """
    return await async_proxy_manager.create_session(timeout=timeout, headers=headers)


async def test_proxy() -> bool:
    """
    Convenience function to test proxy
    
    Returns:
        True if proxy test successful
    """
    return await async_proxy_manager.test_connection()


def get_proxy_status() -> dict:
    """
    Convenience function to get proxy status
    
    Returns:
        Dictionary with proxy status
    """
    return async_proxy_manager.get_status()