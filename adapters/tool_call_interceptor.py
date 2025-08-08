#!/usr/bin/env python3
"""
Tool call interceptor that wraps amp to capture structured tool usage.
Creates a JSON log of tool calls for evaluation purposes.
"""

import json
import subprocess
import time
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, List


class ToolCallInterceptor:
    """Intercepts and logs tool calls from amp execution."""
    
    def __init__(self):
        self.tool_log_file = None
        
    def create_interceptor_script(self) -> str:
        """Create a wrapper script that logs tool calls."""
        script_content = '''#!/usr/bin/env python3
import sys
import json
import time
import os
from pathlib import Path

# Tool call logger
def log_tool_call(tool_name: str, args: dict, result: str = ""):
    log_entry = {
        "timestamp": time.time(),
        "tool": tool_name,
        "arguments": args,
        "result_preview": result[:200] if result else "",
        "success": True
    }
    
    log_file = os.environ.get("AMP_TOOL_LOG_FILE")
    if log_file:
        try:
            with open(log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\\n")
        except Exception:
            pass

# Monkey patch common tool patterns
original_subprocess_run = subprocess.run

def patched_subprocess_run(*args, **kwargs):
    result = original_subprocess_run(*args, **kwargs)
    
    # Try to detect tool usage from command patterns
    if args and len(args[0]) > 0:
        cmd_str = " ".join(args[0]) if isinstance(args[0], list) else str(args[0])
        
        if "rg " in cmd_str or "ripgrep" in cmd_str:
            log_tool_call("Grep", {"pattern": "detected"}, result.stdout if hasattr(result, 'stdout') else "")
        elif "find " in cmd_str and "-name" in cmd_str:
            log_tool_call("glob", {"filePattern": "detected"}, result.stdout if hasattr(result, 'stdout') else "")
    
    return result

import subprocess
subprocess.run = patched_subprocess_run

# Now execute the original amp command
import sys
os.execvp(sys.argv[1], sys.argv[1:])
'''
        
        # Write the interceptor script
        script_path = tempfile.mktemp(suffix='.py', prefix='amp_interceptor_')
        with open(script_path, 'w') as f:
            f.write(script_content)
        os.chmod(script_path, 0o755)
        
        return script_path
    
    def run_with_interception(self, cmd: List[str]) -> Dict[str, Any]:
        """Run amp command with tool call interception."""
        # Create temporary log file
        log_fd, self.tool_log_file = tempfile.mkstemp(suffix='.jsonl', prefix='amp_tools_')
        os.close(log_fd)
        
        # Set up environment
        env = os.environ.copy()
        env['AMP_TOOL_LOG_FILE'] = self.tool_log_file
        
        try:
            # Run the command directly - amp handles its own tool dispatch
            result = subprocess.run(cmd, capture_output=True, text=True, env=env)
            
            # Parse the tool log
            tool_calls = self._parse_tool_log()
            
            return {
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode,
                'tool_calls': tool_calls
            }
            
        finally:
            # Cleanup
            if self.tool_log_file and os.path.exists(self.tool_log_file):
                os.unlink(self.tool_log_file)
    
    def _parse_tool_log(self) -> List[Dict[str, Any]]:
        """Parse the tool call log file."""
        tool_calls = []
        
        if not self.tool_log_file or not os.path.exists(self.tool_log_file):
            return tool_calls
            
        try:
            with open(self.tool_log_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        tool_calls.append({
                            'name': entry.get('tool', 'unknown'),
                            'arguments': entry.get('arguments', {}),
                            'timestamp': entry.get('timestamp')
                        })
                    except json.JSONDecodeError:
                        continue
                        
        except Exception:
            pass
            
        return tool_calls


if __name__ == "__main__":
    interceptor = ToolCallInterceptor()
    result = interceptor.run_with_interception(['amp', '-x', 'List Python files'])
    print(json.dumps(result, indent=2))
