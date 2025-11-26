import logging
import time
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MonitoringService:
    """
    Service responsible for monitoring performance and logging events.
    """

    def log_event(self, event_type: str, details: Dict[str, Any]):
        """Logs a structured event."""
        logger.info(f"EVENT: {event_type} - {details}")

    def log_performance(self, operation: str, start_time: float):
        """Logs the duration of an operation."""
        duration = time.time() - start_time
        logger.info(f"PERFORMANCE: {operation} took {duration:.4f} seconds")

    def log_error(self, operation: str, error: Exception):
        """Logs an error."""
        logger.error(f"ERROR in {operation}: {error}")
