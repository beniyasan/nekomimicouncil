from pydantic_settings import BaseSettings
from typing import List, Literal
import os

class Settings(BaseSettings):
    # AI Provider Configuration
    ai_provider: Literal["openai", "anthropic", "mixed"] = "mixed"
    
    # OpenAI Configuration
    openai_api_key: str = ""
    openai_model_debate: str = "gpt-4o-mini"
    openai_model_officer: str = "gpt-o3-pro"
    
    # Anthropic Configuration
    anthropic_api_key: str = ""
    anthropic_model_debate: str = "claude-3-5-haiku-20241022"
    anthropic_model_officer: str = "claude-sonnet-4-20250514"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: List[str] = ["http://localhost:3000"]
    
    # Debate Configuration
    max_tokens_debate: int = 128
    max_tokens_officer: int = 256
    debate_timeout_seconds: int = 30
    max_concurrent_debates: int = 5
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Development
    debug: bool = True
    reload: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables

# Global settings instance
settings = Settings()