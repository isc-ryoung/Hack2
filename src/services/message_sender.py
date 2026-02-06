"""Message sender service for transmitting error messages to external systems.

Handles formatting and transmission of IRIS error messages to external consumers.
"""

import json
from typing import Optional
import requests

from src.models.error_message import ErrorMessage
from src.utils.config import get_config
from src.utils.logger import get_logger


logger = get_logger(__name__)


class MessageSenderService:
    """Service for sending error messages to external endpoints."""
    
    def __init__(self, output_endpoint: Optional[str] = None):
        """Initialize message sender.
        
        Args:
            output_endpoint: URL of external message consumer (overrides config)
        """
        config = get_config()
        self.endpoint = output_endpoint or config.external.message_endpoint
        self.timeout = 10  # seconds
        self.message_queue = []
    
    def send_message(self, error: ErrorMessage) -> dict:
        """Send error message to external system.
        
        Args:
            error: ErrorMessage to send
            
        Returns:
            Dictionary with status and details
        """
        logger.info(
            "message_send_start",
            endpoint=self.endpoint,
            severity=error.severity,
            category=error.category
        )
        
        try:
            # Format message for external consumption
            payload = {
                "timestamp": error.timestamp,
                "process_id": error.process_id,
                "severity": error.severity,
                "category": error.category,
                "message": error.message_text,
                "log_format": error.to_log_format()
            }
            
            # Send to external endpoint
            response = requests.post(
                self.endpoint,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                logger.info(
                    "message_send_success",
                    endpoint=self.endpoint,
                    status_code=response.status_code
                )
                return {
                    "status": "success",
                    "endpoint": self.endpoint,
                    "response_code": response.status_code
                }
            else:
                logger.warning(
                    "message_send_failed",
                    endpoint=self.endpoint,
                    status_code=response.status_code
                )
                # Queue for retry
                self.message_queue.append(error)
                return {
                    "status": "failed",
                    "endpoint": self.endpoint,
                    "response_code": response.status_code,
                    "queued": True
                }
        
        except requests.exceptions.RequestException as e:
            logger.error(
                "message_send_error",
                endpoint=self.endpoint,
                error=str(e)
            )
            # Queue message for retry
            self.message_queue.append(error)
            return {
                "status": "error",
                "error": str(e),
                "queued": True
            }
    
    def get_queue_size(self) -> int:
        """Get number of queued messages.
        
        Returns:
            Queue size
        """
        return len(self.message_queue)
    
    def retry_queued_messages(self) -> dict:
        """Retry sending queued messages.
        
        Returns:
            Dictionary with retry results
        """
        if not self.message_queue:
            return {"status": "no_messages", "count": 0}
        
        logger.info(
            "retry_queued_start",
            queue_size=len(self.message_queue)
        )
        
        success_count = 0
        failed_count = 0
        remaining_queue = []
        
        for error in self.message_queue:
            result = self.send_message(error)
            if result["status"] == "success":
                success_count += 1
            else:
                failed_count += 1
                remaining_queue.append(error)
        
        self.message_queue = remaining_queue
        
        logger.info(
            "retry_queued_complete",
            success_count=success_count,
            failed_count=failed_count,
            remaining_queue=len(self.message_queue)
        )
        
        return {
            "status": "completed",
            "success_count": success_count,
            "failed_count": failed_count,
            "remaining_queue": len(self.message_queue)
        }
