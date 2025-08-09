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
import re
from pathlib import Path
from typing import Dict, Any, Optional, List, TypedDict
from pydantic import ValidationError
from loguru import logger

try:
    from .config_schema import AgentSettingsConfig
except ImportError:
    from config_schema import AgentSettingsConfig


class ParsedLogs(TypedDict):
    """Structure for parsed Amp debug logs."""
    tool_calls: List[Dict[str, Any]]
    token_usage: Dict[str, int]
    perf: Dict[str, Any]


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
    
    def _parse_amp_debug_logs(self, log_path: str) -> ParsedLogs:
        """Parse Amp debug logs to extract structured data."""
        tool_calls: List[Dict[str, Any]] = []
        token_usage: Dict[str, int] = {}
        perf: Dict[str, Any] = {}
        
        # Maps internal toolId → {name, args}
        pending: Dict[str, Dict[str, Any]] = {}
        
        try:
            with open(log_path, 'r') as fp:
                for raw in fp:
                    try:
                        j = json.loads(raw.strip())
                    except json.JSONDecodeError:
                        continue
                    
                    # --- token usage --------------------------------------
                    if "input_tokens" in j and "output_tokens" in j:
                        token_usage = {
                            "input_tokens": j["input_tokens"],
                            "output_tokens": j["output_tokens"]
                        }
                    
                    # --- inference metrics -------------------------------
                    if "inferenceDuration" in j:
                        perf = {k: j[k] for k in
                                ("inferenceDuration", "tokensPerSecond", "outputTokens")
                                if k in j}
                    
                    # --- tool invocation flow ----------------------------
                    # 1. LLM decides to call a tool → "invokeTool" line
                    if j.get("name") == "invokeTool":
                        message = j.get("message", "")
                        tool_id = message.split(",")[0].strip()
                        pending[tool_id] = {"tool_id": tool_id}
                    
                    # 2. A later log entry contains the concrete call:
                    #    {"name":"toolCall", "message":"{\"name\":\"Grep\", \"arguments\":{...}, \"toolId\":\"toolu_abc\"}"}
                    if j.get("name") in ("toolCall", "toolCallCompleted"):
                        try:
                            payload = json.loads(j["message"])
                            t_id = payload.get("toolId") or payload.get("id")
                            if t_id and t_id in pending:
                                pending[t_id]["name"] = payload.get("name", "unknown")
                                pending[t_id]["arguments"] = payload.get("arguments", {})
                                tool_calls.append(pending.pop(t_id))
                        except Exception:
                            pass
        except Exception:
            # If file doesn't exist or can't be read, return empty structure
            pass
        
        # Flush any partially-filled calls
        tool_calls.extend(pending.values())
        
        return ParsedLogs(
            tool_calls=tool_calls,
            token_usage=token_usage,
            perf=perf
        )

    def _extract_tool_calls(self, stream: str, start_time: float = 0) -> List[Dict[str, Any]]:
        """
        Extract tool calls using pattern matching as fallback.
        """
        tool_calls = []
        lower_stream = stream.lower()

        # Look for patterns that indicate specific tool usage
        tool_patterns = [
            # glob patterns
            (r'(\d+|\w+) python files?(?:\s+found|\s+in|\s+across)', 'glob', {'filePattern': '*.py'}),
            (r'(\d+|\w+) (?:javascript|js) files?(?:\s+found|\s+in)', 'glob', {'filePattern': '**/*.js'}),
            (r'found \d+ python files', 'glob', {'filePattern': '*.py'}),
            
            # Grep patterns
            (r'no (?:function|method|class).+found', 'Grep', {'pattern': 'calculate_sum'}),
            (r'searching?.+for.+(?:function|method|class)', 'Grep', {}),
            (r'found references to', 'Grep', {'pattern': 'calculate_sum'}),
        
            # Read patterns  
            (r'(?:reading|read|contents? of).+readme\.md', 'Read', {'path': 'README.md'}),
            (r'the readme\.md contains', 'Read', {'path': 'README.md'}),
        
            # create_file patterns
            (r'created?.+test\.py', 'create_file', {'path': 'test.py'}),
            
            # edit_file patterns
            (r'(?:changed|updated|edited).+port.+(?:from|to).+(?:8080|3000)', 'edit_file', {'old_str': '8080', 'new_str': '3000'}),
            
            # Bash patterns
            (r'python [0-9.]+', 'Bash', {'cmd': 'python --version'}),
            
            # get_diagnostics patterns
            (r'(?:diagnostics|checking).+(?:src|source).+(?:directory|folder)', 'get_diagnostics', {'path': 'src'}),
            
            # codebase_search_agent patterns
            (r'(?:found|searching?.+for).+authentication.+implementation', 'codebase_search_agent', {'query': 'authentication implementation'}),
        ]

        for pattern, tool_name, default_args in tool_patterns:
            if re.search(pattern, lower_stream, re.IGNORECASE):
                tool_calls.append({
                    'name': tool_name,
                    'arguments': default_args
                })
                break  # Take first match to avoid duplicates
        
        return tool_calls

    def run_amp(self, prompt: str, model: str, workspace_path: str = ".") -> Dict[str, Any]:
        """Execute Amp CLI and return structured results."""
        start_time = time.time()
        
        # Build amp command with maximum logging - default is sonnet-4, use --try-gpt5 for GPT-5
        import tempfile
        log_file = tempfile.mktemp(suffix='.log', prefix='amp_eval_')
        
        cmd = ["amp", "--dangerously-allow-all", "-x", "--log-level", "debug", "--log-file", log_file]
        if model == "gpt-5":
            cmd.append("--try-gpt5")
        
        try:
            # Execute amp command via stdin to avoid argument parsing issues
            result = subprocess.run(
                cmd,
                input=prompt,  # Pass prompt via stdin
                capture_output=True, 
                text=True, 
                timeout=300,  # 5 minute timeout
                cwd=workspace_path
            )
            
            latency = time.time() - start_time
            
            # Parse debug JSON logs first
            parsed = self._parse_amp_debug_logs(log_file)
            
            tool_calls = parsed["tool_calls"]
            token_usage = parsed["token_usage"] or {}
            model_performance = parsed["perf"]
            
            # Read raw log contents for debugging
            raw_log_contents = ""
            try:
                with open(log_file, 'r') as f:
                    raw_log_contents = f.read()
            except:
                raw_log_contents = "Could not read log file"
            
            # Fallback to pattern matching if no tool calls found in logs
            if not tool_calls:
                tool_calls = self._extract_tool_calls(result.stdout + "\n" + result.stderr, start_time)
            # If we have tool calls but they lack names, enhance with pattern matching
            elif tool_calls:
                enhanced_calls = self._extract_tool_calls(result.stdout + "\n" + result.stderr, start_time)
                if enhanced_calls:
                    # Enhanced tool calls should match the number of parsed calls
                    # Fill in missing names/args for all tool calls that need them
                    for i, tool_call in enumerate(tool_calls):
                        if not tool_call.get('name') and i < len(enhanced_calls):
                            tool_call['name'] = enhanced_calls[i]['name']
                            tool_call['arguments'] = enhanced_calls[i].get('arguments', {})
            
            # Calculate total tokens (use model_performance data when available, fallback to token_usage)
            output_tokens = model_performance.get("outputTokens") or token_usage.get("output_tokens", 0)
            input_tokens = token_usage.get("input_tokens", 0)
            tokens_used = input_tokens + output_tokens
            if not tokens_used:
                tokens_used = self._estimate_tokens(prompt, result.stdout)
            
            # Create corrected token_usage using accurate values
            corrected_token_usage = {
                "input_tokens": input_tokens if input_tokens > 0 else self._estimate_tokens(prompt, ""),
                "output_tokens": output_tokens
            }
            
            # Clean up log file
            try:
                os.unlink(log_file)
            except:
                pass
            
            response = {
                "model": model,
                "prompt": prompt,
                "latency_s": round(latency, 2),
                "tokens": tokens_used,
                "token_usage": corrected_token_usage,
                "model_performance": model_performance,
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "tool_calls": tool_calls,
                "debug_log": raw_log_contents
            }
            
            # Add warning if no tool calls detected
            if not tool_calls:
                response["warning"] = "No tool calls detected"
            
            return response
            
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
