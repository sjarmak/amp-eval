#!/usr/bin/env python3
"""
OpenAI-Evals compatible adapter for Amp CLI.
Implements model selection logic and wraps Amp execution.
"""

import os
import yaml
import json
import time
import subprocess
import argparse
from typing import Dict, Any, Optional
from pydantic import ValidationError
from loguru import logger

try:
    from .config_schema import AgentSettingsConfig
except ImportError:
    from config_schema import AgentSettingsConfig


class AmpRunner:
    """Wrapper for Amp CLI compatible with OpenAI-Evals registry."""
    
    def __init__(self, config_path: str = "config/agent_settings.yaml"):
        """Initialize with configuration."""
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load and validate agent settings configuration."""
        try:
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Validate configuration with Pydantic
            try:
                validated_config = AgentSettingsConfig(**config_data)
                logger.info(f"Configuration loaded and validated successfully from {self.config_path}")
                return validated_config.model_dump()
            except ValidationError as e:
                logger.error(f"Configuration validation failed: {e}")
                logger.warning("Falling back to default configuration")
                return self._get_default_config()
                
        except FileNotFoundError:
            logger.warning(f"Configuration file not found: {self.config_path}")
            logger.info("Using default configuration")
            return self._get_default_config()
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error in {self.config_path}: {e}")
            logger.warning("Falling back to default configuration")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get fallback default configuration."""
        return {
            'default_model': 'sonnet-4',
            'oracle_trigger': {'phrase': 'consult the oracle:', 'model': 'o3'},
            'cli_flag_gpt5': {'flag': '--try-gpt5', 'model': 'gpt-5'},
            'env_var': {'name': 'AMP_MODEL', 'valid_values': ['sonnet-4', 'gpt-5', 'o3']},
            'rules': []
        }
    
    def select_model(self, prompt: str, cli_args: Optional[list] = None, 
                     diff_lines: int = 0, touched_files: int = 0) -> str:
        """Apply model selection logic based on configuration precedence."""
        cli_args = cli_args or []
        
        # 1. Oracle trigger (highest priority)
        oracle_phrase = self.config['oracle_trigger']['phrase']
        if prompt.strip().lower().startswith(oracle_phrase.lower()):
            return self.config['oracle_trigger']['model']
        
        # 2. CLI flag override
        gpt5_flag = self.config['cli_flag_gpt5']['flag']
        if gpt5_flag in cli_args:
            return self.config['cli_flag_gpt5']['model']
        
        # 3. Environment variable
        env_var = self.config['env_var']['name']
        env_model = os.getenv(env_var)
        if env_model and env_model in self.config['env_var']['valid_values']:
            return env_model
        
        # 4. Rules evaluation
        for rule in self.config.get('rules', []):
            if self._evaluate_rule(rule, diff_lines, touched_files):
                return rule['target_model']
        
        # 5. Default fallback
        return self.config['default_model']
    
    def _evaluate_rule(self, rule: Dict[str, Any], diff_lines: int, touched_files: int) -> bool:
        """Evaluate a single rule condition."""
        condition = rule['condition']
        
        # Simple condition parsing for demo
        if 'diff_lines > 40' in condition and diff_lines > 40:
            return True
        if 'touched_files > 2' in condition and touched_files > 2:
            return True
        if 'AND' in condition:
            # Both conditions must be true
            return diff_lines > 40 and touched_files > 2
        
        return False
    
    def run_amp(self, prompt: str, model: str, workspace_path: str = ".") -> Dict[str, Any]:
        """Execute Amp CLI and return structured results."""
        start_time = time.time()
        
        # Build amp command - default is sonnet-4, use --try-gpt5 for GPT-5
        cmd = ["amp", "-x"]
        if model == "gpt-5":
            cmd.append("--try-gpt5")
        cmd.append(prompt)
        
        try:
            
            # Execute amp command
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=300,  # 5 minute timeout
                cwd=workspace_path
            )
            
            latency = time.time() - start_time
            
            # Parse response for token usage (mock for now)
            tokens_used = self._estimate_tokens(prompt, result.stdout)
            
            return {
                "model": model,
                "latency_s": round(latency, 2),
                "tokens": tokens_used,
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                "model": model,
                "latency_s": 300.0,
                "tokens": 0,
                "success": False,
                "error": "Timeout exceeded",
                "stdout": "",
                "stderr": "Command timed out after 300 seconds"
            }
        except Exception as e:
            return {
                "model": model,
                "latency_s": time.time() - start_time,
                "tokens": 0,
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": str(e)
            }
    
    def _estimate_tokens(self, prompt: str, response: str) -> int:
        """Rough token estimation (replace with actual tokenizer)."""
        # Simple approximation: ~4 chars per token
        return (len(prompt) + len(response)) // 4
    
    def evaluate(self, prompt: str, workspace_path: str = ".", 
                 cli_args: Optional[list] = None, **kwargs) -> Dict[str, Any]:
        """Main evaluation entry point for OpenAI-Evals."""
        # Extract metrics from kwargs if provided
        diff_lines = kwargs.get('diff_lines', 0)
        touched_files = kwargs.get('touched_files', 0)
        
        # Select appropriate model
        model = self.select_model(prompt, cli_args, diff_lines, touched_files)
        
        # Execute and return results
        return self.run_amp(prompt, model, workspace_path)


def register_amp_runner():
    """OpenAI-Evals registry entry point."""
    return AmpRunner()


def main():
    """CLI interface for testing."""
    parser = argparse.ArgumentParser(description="Amp Model Evaluation Runner")
    parser.add_argument("prompt", help="Prompt to send to Amp")
    parser.add_argument("--workspace", default=".", help="Workspace path")
    parser.add_argument("--try-gpt5", action="store_true", help="Force GPT-5 model")
    parser.add_argument("--diff-lines", type=int, default=0, help="Number of diff lines")
    parser.add_argument("--touched-files", type=int, default=0, help="Number of touched files")
    
    args = parser.parse_args()
    
    runner = AmpRunner()
    cli_args = ['--try-gpt5'] if args.try_gpt5 else []
    
    result = runner.evaluate(
        args.prompt, 
        args.workspace, 
        cli_args,
        diff_lines=args.diff_lines,
        touched_files=args.touched_files
    )
    
    logger.info(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
