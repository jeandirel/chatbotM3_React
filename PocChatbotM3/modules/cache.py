import logging
from typing import Optional, Any
from cachetools import TTLCache

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CacheService:
    """
    Service responsible for caching query results to improve performance.
    Uses an in-memory TTL (Time-To-Live) cache.
    """

    def __init__(self, maxsize: int = 1000, ttl: int = 300):
        # Default: 1000 items, expire after 5 minutes (300 seconds)
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)
        logger.info(f"Cache initialized (maxsize={maxsize}, ttl={ttl}s)")

    def get(self, key: str) -> Optional[Any]:
        """Retrieves a value from the cache."""
        value = self.cache.get(key)
        if value:
            logger.debug(f"Cache hit for key: {key}")
        else:
            logger.debug(f"Cache miss for key: {key}")
        return value

    def set(self, key: str, value: Any):
        """Sets a value in the cache."""
        self.cache[key] = value
        logger.debug(f"Cache set for key: {key}")

    def clear(self):
        """Clears the cache."""
        self.cache.clear()
        logger.info("Cache cleared.")
