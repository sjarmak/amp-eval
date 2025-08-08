#!/usr/bin/env python3
"""
Model runners package for extensible model support.
"""

from .base import (
    BaseModelRunner,
    ModelConfig,
    ModelResponse,
    ModelProvider,
    ModelRunnerFactory
)

# Import all runner implementations to register them
from .openai_runner import OpenAIRunner
from .anthropic_runner import AnthropicRunner
from .local_runner import LocalGGUFRunner

__all__ = [
    "BaseModelRunner",
    "ModelConfig", 
    "ModelResponse",
    "ModelProvider",
    "ModelRunnerFactory",
    "OpenAIRunner",
    "AnthropicRunner", 
    "LocalGGUFRunner"
]
