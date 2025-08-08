#!/usr/bin/env python3
"""
Dynamic evaluation loading and model switching.
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from ..models import ModelConfig, ModelProvider, ModelRunnerFactory, BaseModelRunner
from ..graders import GraderPluginLoader, BaseGrader


@dataclass
class EvaluationSpec:
    """Specification for a single evaluation."""
    name: str
    description: str
    tasks: List[Dict[str, Any]]
    grading: Dict[str, Any]
    metadata: Dict[str, Any]
    version: str = "1.0"
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'EvaluationSpec':
        """Load evaluation spec from YAML file."""
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        
        return cls(
            name=data.get('name', Path(yaml_path).stem),
            description=data.get('description', ''),
            tasks=data.get('tasks', []),
            grading=data.get('grading', {}),
            metadata=data.get('metadata', {}),
            version=data.get('version', '1.0')
        )


class DynamicEvaluationLoader:
    """Loads and manages evaluation suites dynamically."""
    
    def __init__(self, eval_directory: str = "evals"):
        self.eval_directory = Path(eval_directory)
        self.loaded_evaluations = {}
        self.model_runners = {}
        self.grader_loader = GraderPluginLoader()
    
    def discover_evaluations(self) -> List[str]:
        """Discover all evaluation YAML files."""
        if not self.eval_directory.exists():
            return []
        
        eval_files = []
        for yaml_file in self.eval_directory.glob("*.yaml"):
            eval_files.append(str(yaml_file))
        
        return sorted(eval_files)
    
    def load_evaluation(self, eval_path: str) -> EvaluationSpec:
        """Load a single evaluation specification."""
        if eval_path in self.loaded_evaluations:
            return self.loaded_evaluations[eval_path]
        
        spec = EvaluationSpec.from_yaml(eval_path)
        self.loaded_evaluations[eval_path] = spec
        
        return spec
    
    def load_all_evaluations(self) -> Dict[str, EvaluationSpec]:
        """Load all discovered evaluations."""
        evaluations = {}
        
        for eval_path in self.discover_evaluations():
            try:
                spec = self.load_evaluation(eval_path)
                evaluations[spec.name] = spec
            except Exception as e:
                print(f"Failed to load evaluation {eval_path}: {e}")
        
        return evaluations
    
    def setup_model_runner(self, model_name: str, provider: str, **config_kwargs) -> BaseModelRunner:
        """Setup a model runner for the given configuration."""
        runner_key = f"{provider}_{model_name}"
        
        if runner_key in self.model_runners:
            return self.model_runners[runner_key]
        
        # Create model config
        config = ModelConfig(
            name=model_name,
            provider=ModelProvider(provider),
            model_id=model_name,
            **config_kwargs
        )
        
        # Create runner
        runner = ModelRunnerFactory.create_runner(config)
        
        # Initialize runner
        if not runner.initialize():
            raise RuntimeError(f"Failed to initialize model runner for {model_name}")
        
        self.model_runners[runner_key] = runner
        return runner
    
    def get_grader_for_evaluation(self, eval_path: str) -> Optional[BaseGrader]:
        """Get custom grader for an evaluation."""
        return self.grader_loader.load_grader_for_evaluation(eval_path)
    
    def run_evaluation(self, eval_name: str, model_config: Dict[str, Any], 
                      task_filter: Optional[str] = None) -> Dict[str, Any]:
        """Run a specific evaluation with the given model."""
        # Load evaluation spec
        eval_spec = None
        for eval_path, spec in self.loaded_evaluations.items():
            if spec.name == eval_name:
                eval_spec = spec
                break
        
        if not eval_spec:
            # Try to load it dynamically
            eval_files = self.discover_evaluations()
            for eval_path in eval_files:
                if eval_name in eval_path:
                    eval_spec = self.load_evaluation(eval_path)
                    break
        
        if not eval_spec:
            raise ValueError(f"Evaluation '{eval_name}' not found")
        
        # Setup model runner
        runner = self.setup_model_runner(**model_config)
        
        # Load custom grader if available
        custom_grader = None
        for eval_path in self.loaded_evaluations:
            if self.loaded_evaluations[eval_path].name == eval_name:
                custom_grader = self.get_grader_for_evaluation(eval_path)
                break
        
        # Run tasks
        results = {
            "evaluation": eval_name,
            "model": model_config,
            "tasks": [],
            "summary": {}
        }
        
        for task in eval_spec.tasks:
            # Skip if task filter specified and doesn't match
            if task_filter and task_filter not in task.get("name", ""):
                continue
            
            task_result = self._run_single_task(task, runner, custom_grader)
            results["tasks"].append(task_result)
        
        # Calculate summary metrics
        results["summary"] = self._calculate_summary(results["tasks"])
        
        return results
    
    def _run_single_task(self, task: Dict[str, Any], runner: BaseModelRunner, 
                        custom_grader: Optional[BaseGrader] = None) -> Dict[str, Any]:
        """Run a single evaluation task."""
        prompt = task.get("prompt", "")
        expected = task.get("expected")
        task_name = task.get("name", "unnamed_task")
        
        # Run model
        response = runner.run(prompt)
        
        # Grade response
        if custom_grader:
            # Use custom grader
            grade_result = custom_grader.grade(response.content, expected, task)
        else:
            # Use default grading logic
            grade_result = self._default_grade(response.content, expected, task)
        
        return {
            "name": task_name,
            "prompt": prompt,
            "response": response.content,
            "expected": expected,
            "grade": {
                "score": grade_result.score,
                "max_score": grade_result.max_score,
                "passed": grade_result.passed,
                "feedback": grade_result.feedback,
                "details": grade_result.details
            },
            "model_metrics": {
                "tokens_used": response.tokens_used,
                "latency_s": response.latency_s,
                "success": response.success
            }
        }
    
    def _default_grade(self, response: str, expected: Any, context: Dict[str, Any]) -> Any:
        """Default grading when no custom grader is available."""
        from ..graders import GradeResult
        
        if expected is None:
            return GradeResult(
                score=1.0 if response.strip() else 0.0,
                max_score=1.0,
                passed=bool(response.strip()),
                feedback="No expected value - graded on presence of response"
            )
        
        # Simple contains check
        contains = str(expected).lower() in response.lower()
        return GradeResult(
            score=1.0 if contains else 0.0,
            max_score=1.0,
            passed=contains,
            feedback=f"Response {'contains' if contains else 'missing'} expected content"
        )
    
    def _calculate_summary(self, task_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary metrics for all tasks."""
        if not task_results:
            return {}
        
        total_tasks = len(task_results)
        passed_tasks = sum(1 for task in task_results if task["grade"]["passed"])
        total_score = sum(task["grade"]["score"] for task in task_results)
        max_score = sum(task["grade"]["max_score"] for task in task_results)
        
        total_tokens = sum(task["model_metrics"]["tokens_used"] for task in task_results)
        avg_latency = sum(task["model_metrics"]["latency_s"] for task in task_results) / total_tasks
        
        return {
            "total_tasks": total_tasks,
            "passed_tasks": passed_tasks,
            "pass_rate": passed_tasks / total_tasks if total_tasks > 0 else 0,
            "total_score": total_score,
            "max_score": max_score,
            "score_percentage": (total_score / max_score * 100) if max_score > 0 else 0,
            "total_tokens": total_tokens,
            "avg_latency_s": round(avg_latency, 2),
            "successful_runs": sum(1 for task in task_results if task["model_metrics"]["success"])
        }
    
    def list_models(self) -> Dict[str, List[str]]:
        """List available models by provider."""
        return {
            "openai": ["gpt-4o", "gpt-4o-mini", "o1-preview", "o1-mini"],
            "anthropic": ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022"],
            "local_gguf": ["custom-model"]  # Depends on what's running locally
        }
    
    def health_check(self) -> Dict[str, bool]:
        """Check health of all configured model runners."""
        health_status = {}
        
        for runner_key, runner in self.model_runners.items():
            try:
                health_status[runner_key] = runner.health_check()
            except Exception:
                health_status[runner_key] = False
        
        return health_status
    
    def clear_cache(self):
        """Clear all cached evaluations and runners."""
        self.loaded_evaluations.clear()
        self.model_runners.clear()
        self.grader_loader.clear_plugins()


def create_evaluation_template(name: str, output_path: str):
    """Create an evaluation template YAML file."""
    template = {
        "name": name,
        "description": f"Evaluation suite for {name}",
        "version": "1.0",
        "metadata": {
            "author": "Your Name",
            "created": "2024-01-01",
            "tags": ["template"]
        },
        "grading": {
            "type": "custom",  # or "exact_match", "contains", "regex", "function"
            "pass_threshold": 0.7
        },
        "tasks": [
            {
                "name": "task_1",
                "prompt": "Write a function that adds two numbers",
                "expected": "def add(a, b):\n    return a + b",
                "metadata": {
                    "difficulty": "easy",
                    "category": "coding"
                }
            },
            {
                "name": "task_2", 
                "prompt": "Explain what the function does",
                "expected": "addition",
                "metadata": {
                    "difficulty": "easy",
                    "category": "explanation"
                }
            }
        ]
    }
    
    with open(output_path, 'w') as f:
        yaml.dump(template, f, default_flow_style=False, indent=2)
    
    print(f"Created evaluation template: {output_path}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Dynamic evaluation loader utilities")
    parser.add_argument("--create-template", help="Create evaluation template")
    parser.add_argument("--output", help="Output path for template")
    parser.add_argument("--list", action="store_true", help="List available evaluations")
    parser.add_argument("--run", help="Run specific evaluation")
    parser.add_argument("--model", default="gpt-4o-mini", help="Model to use")
    parser.add_argument("--provider", default="openai", help="Model provider")
    
    args = parser.parse_args()
    
    if args.create_template:
        output_path = args.output or f"{args.create_template}.yaml"
        create_evaluation_template(args.create_template, output_path)
    elif args.list:
        loader = DynamicEvaluationLoader()
        evaluations = loader.load_all_evaluations()
        print("Available evaluations:")
        for name, spec in evaluations.items():
            print(f"  - {name}: {spec.description}")
    elif args.run:
        loader = DynamicEvaluationLoader()
        model_config = {
            "model_name": args.model,
            "provider": args.provider
        }
        results = loader.run_evaluation(args.run, model_config)
        print(json.dumps(results, indent=2))
