"""Configuration management from environment variables.

Loads configuration from .env file and provides type-safe access.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


# Load .env file
load_dotenv()


@dataclass
class OpenAIConfig:
    """OpenAI API configuration."""
    api_key: str
    model: str
    fallback_model: str
    timeout_seconds: int
    max_retries: int
    retry_delay_seconds: int


@dataclass
class TokenBudgetConfig:
    """Token budget configuration."""
    per_workflow: int
    per_session: int
    per_day: int
    alert_threshold: float


@dataclass
class ExternalEndpoints:
    """External system endpoint configuration."""
    message_endpoint: str
    command_endpoint: str


@dataclass
class IRISConfig:
    """IRIS database configuration."""
    cpf_path: Path
    instance_name: str


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str
    format: str
    enable_trace_ids: bool


@dataclass
class DevelopmentConfig:
    """Development settings."""
    enable_llm_mocking: bool
    enable_dry_run: bool


class Config:
    """Application configuration."""
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        self.openai = OpenAIConfig(
            api_key=os.getenv('OPENAI_API_KEY', ''),
            model=os.getenv('OPENAI_MODEL', 'gpt-4o-2024-08-06'),
            fallback_model=os.getenv('OPENAI_FALLBACK_MODEL', 'gpt-3.5-turbo'),
            timeout_seconds=int(os.getenv('LLM_TIMEOUT_SECONDS', '30')),
            max_retries=int(os.getenv('LLM_MAX_RETRIES', '3')),
            retry_delay_seconds=int(os.getenv('LLM_RETRY_DELAY_SECONDS', '2')),
        )
        
        self.token_budget = TokenBudgetConfig(
            per_workflow=int(os.getenv('TOKEN_BUDGET_PER_WORKFLOW', '5000')),
            per_session=int(os.getenv('TOKEN_BUDGET_PER_SESSION', '50000')),
            per_day=int(os.getenv('TOKEN_BUDGET_PER_DAY', '500000')),
            alert_threshold=float(os.getenv('BUDGET_ALERT_THRESHOLD', '0.8')),
        )
        
        self.external = ExternalEndpoints(
            message_endpoint=os.getenv('EXTERNAL_MESSAGE_ENDPOINT', 'http://localhost:8080/api/messages'),
            command_endpoint=os.getenv('EXTERNAL_COMMAND_ENDPOINT', 'http://localhost:8080/api/commands'),
        )
        
        self.iris = IRISConfig(
            cpf_path=Path(os.getenv('IRIS_CPF_PATH', '/usr/irissys/iris.cpf')),
            instance_name=os.getenv('IRIS_INSTANCE_NAME', 'IRIS'),
        )
        
        self.logging = LoggingConfig(
            level=os.getenv('LOG_LEVEL', 'INFO'),
            format=os.getenv('LOG_FORMAT', 'json'),
            enable_trace_ids=os.getenv('ENABLE_TRACE_IDS', 'true').lower() == 'true',
        )
        
        self.development = DevelopmentConfig(
            enable_llm_mocking=os.getenv('ENABLE_LLM_MOCKING', 'false').lower() == 'true',
            enable_dry_run=os.getenv('ENABLE_DRY_RUN', 'false').lower() == 'true',
        )
    
    def validate(self) -> list[str]:
        """Validate configuration and return list of errors.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        if not self.openai.api_key:
            errors.append("OPENAI_API_KEY is required")
        
        if self.token_budget.per_workflow <= 0:
            errors.append("TOKEN_BUDGET_PER_WORKFLOW must be positive")
        
        if self.token_budget.per_session < self.token_budget.per_workflow:
            errors.append("TOKEN_BUDGET_PER_SESSION must be >= TOKEN_BUDGET_PER_WORKFLOW")
        
        if self.token_budget.per_day < self.token_budget.per_session:
            errors.append("TOKEN_BUDGET_PER_DAY must be >= TOKEN_BUDGET_PER_SESSION")
        
        return errors


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
        errors = _config.validate()
        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
    return _config
