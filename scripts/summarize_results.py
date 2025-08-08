#!/usr/bin/env python3
"""
Summarize evaluation results for GitHub Actions step summary.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any

def summarize_results(results_file: str) -> None:
    """Generate markdown summary of evaluation results."""
    try:
        with open(results_file) as f:
            results = json.load(f)
        
        # Extract key metrics
        total_tasks = results.get('total_tasks', 0)
        successful_tasks = results.get('successful_tasks', 0)
        accuracy = (successful_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        total_tokens = results.get('total_tokens', 0)
        avg_tokens_per_task = (total_tokens / total_tasks) if total_tasks > 0 else 0
        
        execution_time = results.get('execution_time_seconds', 0)
        
        print(f"""
| Metric | Value |
|--------|-------|
| **Accuracy** | {accuracy:.1f}% ({successful_tasks}/{total_tasks}) |
| **Total Tokens** | {total_tokens:,} |
| **Avg Tokens/Task** | {avg_tokens_per_task:.0f} |
| **Execution Time** | {execution_time:.1f}s |
        """)
        
        # Show task details if available
        if 'task_results' in results:
            print("\n### Task Details")
            for task in results['task_results']:
                status = "✅" if task.get('success', False) else "❌"
                tokens = task.get('tokens_used', 0)
                time = task.get('execution_time', 0)
                print(f"- {status} **{task.get('task_id', 'Unknown')}** ({tokens} tokens, {time:.1f}s)")
                
        # Show errors if any
        errors = results.get('errors', [])
        if errors:
            print(f"\n### Errors ({len(errors)})")
            for error in errors[:3]:  # Show first 3 errors
                print(f"- {error}")
            if len(errors) > 3:
                print(f"- ... and {len(errors) - 3} more")
                
    except Exception as e:
        print(f"❌ Failed to parse results: {e}")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: summarize_results.py <results_file.json>")
        sys.exit(1)
        
    summarize_results(sys.argv[1])
