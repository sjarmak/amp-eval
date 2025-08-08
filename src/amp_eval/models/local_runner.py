#!/usr/bin/env python3
"""
Local GGUF model runner implementation.
"""

import time
import requests
from typing import Dict, Any, Optional

from .base import BaseModelRunner, ModelConfig, ModelResponse, ModelProvider, ModelRunnerFactory


class LocalGGUFRunner(BaseModelRunner):
    """Model runner for local GGUF models via llama.cpp server."""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        # Default to localhost if no base_url provided
        if not self.config.base_url:
            self.config.base_url = "http://localhost:8080"
    
    def initialize(self) -> bool:
        """Check if local server is available."""
        try:
            response = requests.get(
                f"{self.config.base_url}/health",
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Failed to connect to local server: {e}")
            return False
    
    def run(self, prompt: str, **kwargs) -> ModelResponse:
        """Execute prompt with local GGUF model."""
        if not self.health_check():
            return ModelResponse(
                content="",
                model=self.config.model_id,
                tokens_used=0,
                latency_s=0.0,
                success=False,
                error="Local GGUF server not available"
            )
        
        start_time = time.time()
        
        try:
            # Prepare request for llama.cpp server
            request_data = {
                "prompt": prompt,
                "n_predict": kwargs.get("max_tokens", self.config.max_tokens),
                "temperature": kwargs.get("temperature", self.config.temperature),
                "stop": kwargs.get("stop", []),
                "stream": False,
                **self.config.extra_params
            }
            
            # Make API call
            response = requests.post(
                f"{self.config.base_url}/completion",
                json=request_data,
                timeout=self.config.timeout
            )
            
            latency = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("content", "")
                tokens_used = data.get("tokens_predicted", 0) + data.get("tokens_evaluated", 0)
                
                return ModelResponse(
                    content=content,
                    model=self.config.model_id,
                    tokens_used=tokens_used,
                    latency_s=round(latency, 2),
                    success=True,
                    raw_response=data
                )
            else:
                return ModelResponse(
                    content="",
                    model=self.config.model_id,
                    tokens_used=0,
                    latency_s=round(latency, 2),
                    success=False,
                    error=f"HTTP {response.status_code}: {response.text}"
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
        """Estimate token count for local models."""
        # Most GGUF models use similar tokenization to GPT
        return len(text) // 4
    
    def get_model_info(self) -> Dict[str, Any]:
        """Return local model information."""
        # Try to get model info from server
        try:
            response = requests.get(f"{self.config.base_url}/props", timeout=5)
            if response.status_code == 200:
                props = response.json()
                return {
                    "provider": "local_gguf",
                    "model_id": self.config.model_id,
                    "server_url": self.config.base_url,
                    "supports_streaming": True,
                    "supports_function_calling": False,
                    **props
                }
        except Exception:
            pass
        
        return {
            "provider": "local_gguf",
            "model_id": self.config.model_id,
            "server_url": self.config.base_url,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "supports_streaming": True,
            "supports_function_calling": False
        }


# Register the Local GGUF runner
ModelRunnerFactory.register_runner(ModelProvider.LOCAL_GGUF, LocalGGUFRunner)
