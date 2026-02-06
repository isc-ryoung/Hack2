"""OpenAI LLM client wrapper with retry logic and observability.

Provides a unified interface for LLM calls with automatic retries,
timeout handling, and cost tracking.
"""

import time
from typing import Any, Dict, Optional, Type, TypeVar

from openai import OpenAI
from pydantic import BaseModel

from src.utils.config import get_config
from src.utils.cost_tracker import track_tokens
from src.utils.logger import get_logger


logger = get_logger(__name__)
T = TypeVar('T', bound=BaseModel)


class LLMClient:
    """Client for OpenAI LLM interactions with structured outputs."""
    
    def __init__(self):
        """Initialize LLM client."""
        config = get_config()
        self.client = OpenAI(api_key=config.openai.api_key)
        self.model = config.openai.model
        self.fallback_model = config.openai.fallback_model
        self.timeout = config.openai.timeout_seconds
        self.max_retries = config.openai.max_retries
        self.retry_delay = config.openai.retry_delay_seconds
    
    def parse(
        self,
        messages: list[Dict[str, str]],
        response_format: Type[T],
        operation: str = "",
        use_fallback: bool = False,
    ) -> T:
        """Call LLM with structured output parsing.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            response_format: Pydantic model class for response structure
            operation: Operation description for logging
            use_fallback: Use fallback model instead of primary
            
        Returns:
            Parsed response as Pydantic model instance
            
        Raises:
            Exception: If all retries fail
        """
        model = self.fallback_model if use_fallback else self.model
        
        for attempt in range(self.max_retries):
            try:
                start_time = time.time()
                
                logger.info(
                    "llm_request_start",
                    operation=operation,
                    model=model,
                    attempt=attempt + 1,
                    max_retries=self.max_retries,
                )
                
                # Make API call
                response = self.client.beta.chat.completions.parse(
                    model=model,
                    messages=messages,
                    response_format=response_format,
                    timeout=self.timeout,
                )
                
                duration = time.time() - start_time
                
                # Extract parsed result
                parsed = response.choices[0].message.parsed
                
                # Track token usage
                if response.usage:
                    track_tokens(
                        model=model,
                        input_tokens=response.usage.prompt_tokens,
                        output_tokens=response.usage.completion_tokens,
                        operation=operation,
                    )
                
                logger.info(
                    "llm_request_success",
                    operation=operation,
                    model=model,
                    duration_ms=int(duration * 1000),
                    input_tokens=response.usage.prompt_tokens if response.usage else 0,
                    output_tokens=response.usage.completion_tokens if response.usage else 0,
                )
                
                return parsed
            
            except Exception as e:
                logger.warning(
                    "llm_request_failed",
                    operation=operation,
                    model=model,
                    attempt=attempt + 1,
                    error=str(e),
                )
                
                # If this was the last attempt, raise the exception
                if attempt == self.max_retries - 1:
                    logger.error(
                        "llm_request_exhausted",
                        operation=operation,
                        model=model,
                        max_retries=self.max_retries,
                        error=str(e),
                    )
                    raise
                
                # Wait before retrying
                time.sleep(self.retry_delay * (attempt + 1))
        
        raise Exception(f"LLM request failed after {self.max_retries} attempts")
    
    def chat(
        self,
        messages: list[Dict[str, str]],
        operation: str = "",
        use_fallback: bool = False,
        max_tokens: int = 1000,
    ) -> str:
        """Call LLM without structured output (plain text response).
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            operation: Operation description for logging
            use_fallback: Use fallback model instead of primary
            max_tokens: Maximum tokens in response
            
        Returns:
            Response text content
            
        Raises:
            Exception: If all retries fail
        """
        model = self.fallback_model if use_fallback else self.model
        
        for attempt in range(self.max_retries):
            try:
                start_time = time.time()
                
                logger.info(
                    "llm_chat_start",
                    operation=operation,
                    model=model,
                    attempt=attempt + 1,
                )
                
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    timeout=self.timeout,
                )
                
                duration = time.time() - start_time
                content = response.choices[0].message.content
                
                # Track token usage
                if response.usage:
                    track_tokens(
                        model=model,
                        input_tokens=response.usage.prompt_tokens,
                        output_tokens=response.usage.completion_tokens,
                        operation=operation,
                    )
                
                logger.info(
                    "llm_chat_success",
                    operation=operation,
                    model=model,
                    duration_ms=int(duration * 1000),
                )
                
                return content or ""
            
            except Exception as e:
                logger.warning(
                    "llm_chat_failed",
                    operation=operation,
                    attempt=attempt + 1,
                    error=str(e),
                )
                
                if attempt == self.max_retries - 1:
                    logger.error(
                        "llm_chat_exhausted",
                        operation=operation,
                        error=str(e),
                    )
                    raise
                
                time.sleep(self.retry_delay * (attempt + 1))
        
        raise Exception(f"LLM chat failed after {self.max_retries} attempts")


# Global LLM client instance
_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get the global LLM client instance."""
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
