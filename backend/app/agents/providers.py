from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import openai
import anthropic
from ..config import settings
import logging

logger = logging.getLogger(__name__)

class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    @abstractmethod
    async def generate_response(
        self, 
        prompt: str, 
        max_tokens: int = 128,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate a response from the AI model"""
        pass
    
    @abstractmethod
    def get_model_name(self, agent_type: str) -> str:
        """Get the model name for the given agent type"""
        pass

class OpenAIProvider(AIProvider):
    """OpenAI API provider"""
    
    def __init__(self):
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        
        self.client = openai.AsyncOpenAI(
            api_key=settings.openai_api_key
        )
    
    async def generate_response(
        self, 
        prompt: str, 
        max_tokens: int = 128,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate response using OpenAI API"""
        try:
            model = kwargs.get('model', settings.openai_model_debate)
            
            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise
    
    def get_model_name(self, agent_type: str) -> str:
        """Get OpenAI model name for agent type"""
        if agent_type == "officer":
            return settings.openai_model_officer
        return settings.openai_model_debate

class AnthropicProvider(AIProvider):
    """Anthropic API provider"""
    
    def __init__(self):
        if not settings.anthropic_api_key:
            raise ValueError("Anthropic API key not configured")
        
        self.client = anthropic.AsyncAnthropic(
            api_key=settings.anthropic_api_key
        )
    
    async def generate_response(
        self, 
        prompt: str, 
        max_tokens: int = 128,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate response using Anthropic API"""
        try:
            model = kwargs.get('model', settings.anthropic_model_debate)
            
            response = await self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            logger.error(f"Anthropic API error: {str(e)}")
            raise
    
    def get_model_name(self, agent_type: str) -> str:
        """Get Anthropic model name for agent type"""
        if agent_type == "officer":
            return settings.anthropic_model_officer
        return settings.anthropic_model_debate

class AIProviderFactory:
    """Factory for creating AI providers"""
    
    _providers: Dict[str, AIProvider] = {}
    
    @classmethod
    def get_provider(cls, provider_name: str) -> AIProvider:
        """Get or create AI provider instance"""
        if provider_name not in cls._providers:
            if provider_name == "openai":
                cls._providers[provider_name] = OpenAIProvider()
            elif provider_name == "anthropic":
                cls._providers[provider_name] = AnthropicProvider()
            else:
                raise ValueError(f"Unknown provider: {provider_name}")
        
        return cls._providers[provider_name]
    
    @classmethod
    def get_available_providers(cls) -> List[str]:
        """Get list of available providers based on configuration"""
        providers = []
        
        if settings.openai_api_key:
            providers.append("openai")
        if settings.anthropic_api_key:
            providers.append("anthropic")
        
        return providers
    
    @classmethod
    def get_default_provider(cls, agent_type: str = "debate") -> AIProvider:
        """Get default provider based on configuration"""
        available_providers = cls.get_available_providers()
        
        if not available_providers:
            raise ValueError("No AI providers configured")
        
        # Provider selection logic
        if settings.ai_provider == "mixed":
            # For mixed mode, use OpenAI for debates, Anthropic for officer
            if agent_type == "officer" and "anthropic" in available_providers:
                return cls.get_provider("anthropic")
            elif "openai" in available_providers:
                return cls.get_provider("openai")
            else:
                return cls.get_provider(available_providers[0])
        
        elif settings.ai_provider in available_providers:
            return cls.get_provider(settings.ai_provider)
        
        else:
            # Fallback to first available provider
            return cls.get_provider(available_providers[0])