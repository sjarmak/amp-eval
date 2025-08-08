#!/usr/bin/env python3
"""
Base model runner interface for extensible model support.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class ModelProvider(Enum):
    """Supported model providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL_GGUF = "local_gguf"
    CUSTOM = "custom"


@dataclass
class ModelConfig:
    """Configuration for a model instance."""
    name: str
    provider: ModelProvider
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_id: str = ""
    max_tokens: int = 4096
    temperature: float = 0.0
    timeout: int = 300
    extra_params: Dict[str, Any] = None

    def __post_init__(self):
        if self.extra_params is None:
            self.extra_params = {}


@dataclass
class ModelResponse:
    """Standardized response from any model provider."""
    content: str
    model: str
    tokens_used: int
    latency_s: float
    success: bool
    error: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


class BaseModelRunner(ABC):
    """Abstract base class for all model runners."""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self._client = None
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the model client. Returns True if successful."""
        pass
    
    @abstractmethod
    def run(self, prompt: str, **kwargs) -> ModelResponse:
        """Execute a prompt and return standardized response."""
        pass
    
    @abstractmethod
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for the given text."""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Return model information and capabilities."""
        pass
    
    def health_check(self) -> bool:
        """Check if the model is available and responding."""
        try:
            test_response = self.run("Hello", max_tokens=10)
            return test_response.success
        except Exception:
            return False


class ModelRunnerFactory:
    """Factory for creating model runners based on provider."""
    
    _runners = {}
    
    @classmethod
    def register_runner(cls, provider: ModelProvider, runner_class: type):
        """Register a runner class for a specific provider."""
        cls._runners[provider] = runner_class
    
    @classmethod
    def create_runner(cls, config: ModelConfig) -> BaseModelRunner:
        """Create a runner instance for the given configuration."""
        if config.provider not in cls._runners:
            raise ValueError(f"No runner registered for provider: {config.provider}")
        
        runner_class = cls._runners[config.provider]
        return runner_class(config)
    
    @classmethod
    def list_providers(cls) -> List[ModelProvider]:
        """List all registered providers."""
        return list(cls._runners.keys())
