#!/usr/bin/env python3
"""
OpenAI model runner implementation.
"""

import time
import tiktoken
from typing import Dict, Any, Optional
from openai import OpenAI

from .base import BaseModelRunner, ModelConfig, ModelResponse, ModelProvider, ModelRunnerFactory


class OpenAIRunner(BaseModelRunner):
    """Model runner for OpenAI GPT models."""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self._encoding = None
    
    def initialize(self) -> bool:
        """Initialize OpenAI client."""
        try:
            self._client = OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url
            )
            
            # Initialize tokenizer
            try:
                self._encoding = tiktoken.encoding_for_model(self.config.model_id)
            except KeyError:
                # Fallback to cl100k_base for unknown models
                self._encoding = tiktoken.get_encoding("cl100k_base")
            
            return True
        except Exception as e:
            print(f"Failed to initialize OpenAI client: {e}")
            return False
    
    def run(self, prompt: str, **kwargs) -> ModelResponse:
        """Execute prompt with OpenAI model."""
        if not self._client:
            if not self.initialize():
                return ModelResponse(
                    content="",
                    model=self.config.model_id,
                    tokens_used=0,
                    latency_s=0.0,
                    success=False,
                    error="Failed to initialize OpenAI client"
                )
        
        start_time = time.time()
        
        try:
            # Prepare request parameters
            request_params = {
                "model": self.config.model_id,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
                **self.config.extra_params
            }
            
            # Make API call
            response = self._client.chat.completions.create(**request_params)
            
            latency = time.time() - start_time
            
            # Extract response data
            content = response.choices[0].message.content or ""
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            return ModelResponse(
                content=content,
                model=self.config.model_id,
                tokens_used=tokens_used,
                latency_s=round(latency, 2),
                success=True,
                raw_response=response.model_dump()
            )
            
        except Exception as e:
            latency = time.time() - start_time
            return ModelResponse(
                content="",
                model=self.config.model_id,
                tokens_used=0,
                latency_s=round(latency, 2),
                success=False,
                error=str(e)
            )
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count using tiktoken."""
        if not self._encoding:
            # Fallback to character-based estimation
            return len(text) // 4
        
        try:
            return len(self._encoding.encode(text))
        except Exception:
            return len(text) // 4
    
    def get_model_info(self) -> Dict[str, Any]:
        """Return OpenAI model information."""
        return {
            "provider": "openai",
            "model_id": self.config.model_id,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "timeout": self.config.timeout,
            "supports_streaming": True,
            "supports_function_calling": True
        }


# Register the OpenAI runner
ModelRunnerFactory.register_runner(ModelProvider.OPENAI, OpenAIRunner)
