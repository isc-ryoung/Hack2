"""Error Generator Agent using OpenAI Agents SDK.

Generates realistic IRIS error messages based on patterns from messages.log.
"""

from pathlib import Path
from typing import Optional

from agents import Agent, Runner
from pydantic import BaseModel

from src.models.error_message import ErrorMessage, ErrorGenerationRequest
from src.prompts.error_generation import create_error_generation_prompt, FALLBACK_TEMPLATES
from src.services.log_parser import LogParser
from src.utils.logger import get_logger, get_trace_id, set_trace_id
from src.utils.cost_tracker import get_cost_tracker


logger = get_logger(__name__)


class ErrorGeneratorAgentSDK:
    """Error Generator agent using OpenAI Agents SDK."""
    
    def __init__(self, log_samples_path: Optional[Path] = None):
        """Initialize error generator agent.
        
        Args:
            log_samples_path: Path to messages.log file for pattern extraction
        """
        self.agent_name = "error_generator"
        
        # Load log patterns if available
        self.log_parser = None
        if log_samples_path and Path(log_samples_path).exists():
            self.log_parser = LogParser(log_samples_path)
            self.log_parser.parse_log_file()
            logger.info(
                "log_patterns_loaded",
                total_patterns=self.log_parser.total_entries
            )
        
        # Create SDK Agent
        self.agent = Agent(
            name="ErrorGeneratorAgent",
            instructions=self._get_instructions(),
            model="gpt-4o-2024-08-06",
            output_type=ErrorMessage
        )
    
    def _get_instructions(self) -> str:
        """Get agent instructions.
        
        Returns:
            System instructions for the agent
        """
        return """You are an expert at generating realistic InterSystems IRIS database error messages.

Your task is to generate error messages that match the IRIS messages.log format exactly:
Format: MM/DD/YY-HH:MM:SS:mmm (PID) Severity [Category] Message

Rules:
1. Use current timestamp in MM/DD/YY-HH:MM:SS:mmm format
2. Generate realistic process ID (1-999999)
3. Use appropriate severity: 0=info, 1=warning, 2=error, 3=fatal
4. Use [Category.Subcategory] format for category
5. Generate realistic, technical error messages (10-500 characters)

Error Categories:
- license: License key issues, expiration warnings, LMF errors
- config: CPF configuration problems, startup parameter issues
- os: Memory allocation failures, resource exhaustion, file descriptor limits
- journal: Journal file full, I/O errors, sync failures

Generate messages that sound authentic to IRIS database administrators."""
    
    def generate_error(self, request: ErrorGenerationRequest) -> ErrorMessage:
        """Generate an error message.
        
        Args:
            request: Error generation request
            
        Returns:
            Generated ErrorMessage
        """
        # Set trace ID for observability
        if not get_trace_id():
            set_trace_id(f"error-gen-{id(request)}")
        
        logger.info(
            "error_generation_start",
            category=request.error_category,
            severity=request.severity
        )
        
        try:
            # Build prompt with context
            prompt = self._build_prompt(request)
            
            # Run agent (output_type on Agent handles structured output)
            result = Runner.run_sync(
                self.agent,
                prompt
            )
            
            # Extract output
            if hasattr(result, 'final_output'):
                if isinstance(result.final_output, ErrorMessage):
                    error = result.final_output
                elif isinstance(result.final_output, str):
                    # Try to parse as ErrorMessage
                    error = ErrorMessage.model_validate_json(result.final_output)
                else:
                    raise ValueError(f"Unexpected output type: {type(result.final_output)}")
            else:
                # Fallback to template
                logger.warning("agent_no_output_fallback_to_template")
                error = self._generate_with_template(request)
            
            # Track usage
            if hasattr(result, 'usage'):
                tracker = get_cost_tracker()
                tracker.track(
                    input_tokens=result.usage.get('prompt_tokens', 0),
                    output_tokens=result.usage.get('completion_tokens', 0),
                    model=self.agent.model
                )
            
            logger.info(
                "error_generation_complete",
                category=error.category,
                message_preview=error.message_text[:50]
            )
            
            return error
        
        except Exception as e:
            logger.warning(
                "error_generation_failed_fallback",
                error=str(e),
                category=request.error_category
            )
            return self._generate_with_template(request)
    
    def _build_prompt(self, request: ErrorGenerationRequest) -> str:
        """Build prompt for error generation.
        
        Args:
            request: Error generation request
            
        Returns:
            Formatted prompt string
        """
        # Get examples from log parser if available
        examples = []
        if self.log_parser:
            examples = self.log_parser.get_examples(
                category=request.error_category,
                limit=3
            )
        
        # Use prompt template
        return create_error_generation_prompt(
            category=request.error_category,
            severity=request.severity,
            examples=examples
        )
    
    def _generate_with_template(self, request: ErrorGenerationRequest) -> ErrorMessage:
        """Generate error using fallback template.
        
        Args:
            request: Error generation request
            
        Returns:
            Generated ErrorMessage
        """
        import random
        from datetime import datetime
        
        # Get template for category
        templates = FALLBACK_TEMPLATES.get(request.error_category, FALLBACK_TEMPLATES["config"])
        template = random.choice(templates)
        
        # Generate timestamp
        now = datetime.now()
        timestamp = now.strftime("%m/%d/%y-%H:%M:%S:") + f"{now.microsecond // 1000:03d}"
        
        # Generate process ID
        process_id = random.randint(10000, 99999)
        
        # Determine category tag
        category_map = {
            "license": "[Utility.Event]",
            "config": "[Config.Startup]",
            "os": "[System.Resource]",
            "journal": "[Journal.Event]"
        }
        category = category_map.get(request.error_category, "[Generic.Event]")
        
        return ErrorMessage(
            timestamp=timestamp,
            process_id=process_id,
            severity=request.severity,
            category=category,
            message_text=template
        )
