#!/usr/bin/env python3
"""
Anthropic Claude model runner implementation.
"""

import time
from typing import Dict, Any
from anthropic import Anthropic

from .base import BaseModelRunner, ModelConfig, ModelResponse, ModelProvider, ModelRunnerFactory


class AnthropicRunner(BaseModelRunner):
    """Model runner for Anthropic Claude models."""
    
    def initialize(self) -> bool:
        """Initialize Anthropic client."""
        try:
            self._client = Anthropic(
                api_key=self.config.api_key,
                base_url=self.config.base_url
            )
            return True
        except Exception as e:
            print(f"Failed to initialize Anthropic client: {e}")
            return False
    
    def run(self, prompt: str, **kwargs) -> ModelResponse:
        """Execute prompt with Anthropic model."""
        if not self._client:
            if not self.initialize():
                return ModelResponse(
                    content="",
                    model=self.config.model_id,
                    tokens_used=0,
                    latency_s=0.0,
                    success=False,
                    error="Failed to initialize Anthropic client"
                )
        
        start_time = time.time()
        
        try:
            # Prepare request parameters
            request_params = {
                "model": self.config.model_id,
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "messages": [{"role": "user", "content": prompt}],
                **self.config.extra_params
            }
            
            # Make API call
            response = self._client.messages.create(**request_params)
            
            latency = time.time() - start_time
            
            # Extract response data
            content = response.content[0].text if response.content else ""
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            
            return ModelResponse(
                content=content,
                model=self.config.model_id,
                tokens_used=tokens_used,
                latency_s=round(latency, 2),
                success=True,
                raw_response=response.__dict__
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
        """Estimate token count for Anthropic models."""
        # Anthropic uses roughly similar tokenization to OpenAI
        # More accurate estimation would require the official tokenizer
        return len(text) // 3.5  # Slightly more efficient than GPT
    
    def get_model_info(self) -> Dict[str, Any]:
        """Return Anthropic model information."""
        return {
            "provider": "anthropic",
            "model_id": self.config.model_id,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "timeout": self.config.timeout,
            "supports_streaming": True,
            "supports_function_calling": False
        }


# Register the Anthropic runner
ModelRunnerFactory.register_runner(ModelProvider.ANTHROPIC, AnthropicRunner)
