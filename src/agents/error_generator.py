"""Error Generator Agent for creating realistic IRIS error messages.

Generates simulated error messages based on patterns from actual IRIS logs.
"""

import random
from datetime import datetime
from pathlib import Path

from src.agents.base_agent import BaseAgent
from src.models.error_message import ErrorMessage, ErrorGenerationRequest
from src.prompts import get_system_prompt, create_messages
from src.prompts.error_generation import create_error_generation_prompt, FALLBACK_TEMPLATES
from src.services.log_parser import LogParser
from src.utils.llm_client import get_llm_client
from src.utils.logger import get_logger


logger = get_logger(__name__)


class ErrorGeneratorAgent(BaseAgent):
    """Agent for generating realistic IRIS error messages."""
    
    def __init__(self, log_samples_path: Path = None):
        """Initialize error generator agent.
        
        Args:
            log_samples_path: Path to sample messages.log file
        """
        super().__init__("error_generator")
        
        # Initialize log parser
        self.log_parser = LogParser(log_samples_path)
        if log_samples_path and log_samples_path.exists():
            self.log_parser.parse_log_file()
            logger.info(
                "log_patterns_loaded",
                categories=self.log_parser.get_all_categories(),
                total_entries=self.log_parser.total_entries
            )
        else:
            logger.warning(
                "no_log_samples",
                message="No log samples loaded, will use fallback templates"
            )
        
        self.llm_client = get_llm_client()
    
    def _execute_impl(self, input_str: str) -> str:
        """Generate error message based on request.
        
        Args:
            input_str: JSON string with ErrorGenerationRequest
            
        Returns:
            JSON string with ErrorMessage
        """
        # Parse request
        request = ErrorGenerationRequest.model_validate_json(input_str)
        
        logger.info(
            "error_generation_start",
            category=request.error_category,
            severity=request.severity
        )
        
        try:
            # Try LLM-based generation
            error_msg = self._generate_with_llm(request)
        except Exception as e:
            logger.warning(
                "llm_generation_failed",
                error=str(e),
                fallback="Using template-based generation"
            )
            # Fall back to template-based generation
            error_msg = self._generate_with_template(request)
        
        logger.info(
            "error_generation_complete",
            category=request.error_category,
            severity=request.severity,
            message_preview=error_msg.message_text[:50]
        )
        
        return error_msg.model_dump_json()
    
    def _generate_with_llm(self, request: ErrorGenerationRequest) -> ErrorMessage:
        """Generate error using LLM.
        
        Args:
            request: Error generation request
            
        Returns:
            Generated ErrorMessage
        """
        # Get example messages for this category
        examples = self.log_parser.get_examples(request.error_category, count=3)
        
        # Create prompt
        prompt = create_error_generation_prompt(
            error_category=request.error_category,
            severity=request.severity,
            examples=examples,
            context=request.context
        )
        
        # Call LLM with structured output
        messages = create_messages(
            system_prompt=get_system_prompt("error_generator"),
            user_content=prompt
        )
        
        result = self.llm_client.parse(
            messages=messages,
            response_format=ErrorMessage,
            operation=f"generate_{request.error_category}_error"
        )
        
        return result
    
    def _generate_with_template(self, request: ErrorGenerationRequest) -> ErrorMessage:
        """Generate error using template fallback.
        
        Args:
            request: Error generation request
            
        Returns:
            Generated ErrorMessage
        """
        # Get templates for category
        templates = FALLBACK_TEMPLATES.get(request.error_category, FALLBACK_TEMPLATES["config"])
        message_text = random.choice(templates)
        
        # Generate timestamp (current date)
        now = datetime.now()
        timestamp = now.strftime("%m/%d/%y-%H:%M:%S:") + f"{now.microsecond // 1000:03d}"
        
        # Generate random process ID
        process_id = random.randint(10000, 99999)
        
        # Determine category tag
        category_tags = {
            "license": "[Utility.Event]",
            "config": "[config]",
            "os": "[Database]",
            "journal": "[WriteDaemon]"
        }
        category = category_tags.get(request.error_category, "[Generic.Event]")
        
        return ErrorMessage(
            timestamp=timestamp,
            process_id=process_id,
            severity=request.severity,
            category=category,
            message_text=message_text
        )
    
    def generate_error(self, request: ErrorGenerationRequest) -> ErrorMessage:
        """Public API for generating errors (convenience method).
        
        Args:
            request: Error generation request
            
        Returns:
            Generated ErrorMessage
        """
        result_str = self.execute(request.model_dump_json())
        return ErrorMessage.model_validate_json(result_str)
