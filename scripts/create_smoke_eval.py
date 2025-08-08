#!/usr/bin/env python3
"""
Create a smoke evaluation subset with the 3 smallest/fastest tasks.
Used for PR validation and quick feedback cycles.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List

def estimate_task_complexity(task: Dict[str, Any]) -> int:
    """Estimate task complexity based on prompt length and expected operations."""
    prompt_length = len(task.get('input', {}).get('prompt', ''))
    
    # Weight factors
    base_score = prompt_length
    
    # Add complexity for multi-file operations
    if 'files' in str(task.get('input', {})).lower():
        base_score += 100
        
    # Add complexity for test requirements
    if 'test' in str(task.get('input', {})).lower():
        base_score += 50
        
    return base_score

def create_smoke_evaluation():
    """Create smoke.yaml with 3 simplest tasks from existing evaluations."""
    eval_dir = Path('evals')
    smoke_tasks = []
    
    # Collect all tasks from evaluation files
    all_tasks = []
    for eval_file in eval_dir.glob('*.yaml'):
        if eval_file.name == 'smoke.yaml':  # Skip existing smoke eval
            continue
            
        with open(eval_file) as f:
            eval_data = yaml.safe_load(f)
            
        for task in eval_data.get('tasks', []):
            task['source_file'] = eval_file.name
            task['complexity'] = estimate_task_complexity(task)
            all_tasks.append(task)
    
    # Sort by complexity and take 3 simplest
    all_tasks.sort(key=lambda x: x['complexity'])
    smoke_tasks = all_tasks[:3]
    
    # Create smoke evaluation
    smoke_eval = {
        'id': 'amp_eval.smoke',
        'description': 'Smoke test evaluation with 3 smallest tasks for quick validation',
        'disclaimer': 'Auto-generated from existing evaluations for CI/CD pipeline',
        'metrics': ['accuracy', 'token_efficiency', 'first_attempt_success'],
        'tasks': [
            {
                'id': f"smoke_{i+1}",
                'input': task['input'],
                'ideal': task.get('ideal', 'Task completed successfully'),
                'metadata': {
                    'source': task['source_file'],
                    'complexity_score': task['complexity'],
                    'estimated_tokens': min(task['complexity'] * 2, 1000)
                }
            }
            for i, task in enumerate(smoke_tasks)
        ]
    }
    
    # Write smoke evaluation
    smoke_path = eval_dir / 'smoke.yaml'
    with open(smoke_path, 'w') as f:
        yaml.dump(smoke_eval, f, default_flow_style=False, indent=2)
    
    print(f"Created smoke evaluation with {len(smoke_tasks)} tasks:")
    for i, task in enumerate(smoke_tasks, 1):
        print(f"  {i}. {task['source_file']} (complexity: {task['complexity']})")

if __name__ == '__main__':
    create_smoke_evaluation()
