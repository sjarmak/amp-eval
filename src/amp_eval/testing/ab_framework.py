#!/usr/bin/env python3
"""
A/B testing framework for comparing model performance.
"""

import json
import time
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from statistics import mean, stdev
from scipy import stats


@dataclass
class ABTestConfig:
    """Configuration for an A/B test."""
    name: str
    description: str
    model_a: Dict[str, Any]
    model_b: Dict[str, Any]
    evaluations: List[str]
    sample_size: int = 100
    confidence_level: float = 0.95
    randomization_seed: Optional[int] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ABTestResult:
    """Result from an A/B test comparison."""
    config: ABTestConfig
    model_a_results: List[Dict[str, Any]]
    model_b_results: List[Dict[str, Any]]
    statistical_analysis: Dict[str, Any]
    conclusion: str
    timestamp: str
    duration_s: float


class ABTestFramework:
    """Framework for running A/B tests between models."""
    
    def __init__(self, results_directory: str = "results/ab_tests"):
        self.results_dir = Path(results_directory)
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def run_ab_test(self, config: ABTestConfig, 
                   evaluation_loader: Any) -> ABTestResult:
        """Run an A/B test comparing two models."""
        start_time = time.time()
        
        # Set random seed for reproducibility
        if config.randomization_seed:
            random.seed(config.randomization_seed)
        
        print(f"Starting A/B test: {config.name}")
        print(f"Model A: {config.model_a}")
        print(f"Model B: {config.model_b}")
        print(f"Sample size: {config.sample_size}")
        
        # Collect results for both models
        model_a_results = []
        model_b_results = []
        
        for i in range(config.sample_size):
            # Randomize which model goes first to avoid bias
            if random.choice([True, False]):
                result_a = self._run_model_sample(config.model_a, config.evaluations, evaluation_loader, i)
                result_b = self._run_model_sample(config.model_b, config.evaluations, evaluation_loader, i)
            else:
                result_b = self._run_model_sample(config.model_b, config.evaluations, evaluation_loader, i)
                result_a = self._run_model_sample(config.model_a, config.evaluations, evaluation_loader, i)
            
            model_a_results.append(result_a)
            model_b_results.append(result_b)
            
            # Progress update
            if (i + 1) % 10 == 0:
                print(f"Completed {i + 1}/{config.sample_size} samples")
        
        # Perform statistical analysis
        statistical_analysis = self._analyze_results(model_a_results, model_b_results, config.confidence_level)
        
        # Generate conclusion
        conclusion = self._generate_conclusion(statistical_analysis, config)
        
        duration = time.time() - start_time
        
        # Create result object
        result = ABTestResult(
            config=config,
            model_a_results=model_a_results,
            model_b_results=model_b_results,
            statistical_analysis=statistical_analysis,
            conclusion=conclusion,
            timestamp=datetime.now().isoformat(),
            duration_s=round(duration, 2)
        )
        
        # Save results
        self._save_results(result)
        
        print(f"A/B test completed in {duration:.2f}s")
        print(f"Conclusion: {conclusion}")
        
        return result
    
    def _run_model_sample(self, model_config: Dict[str, Any], 
                         evaluations: List[str],
                         evaluation_loader: Any, 
                         sample_id: int) -> Dict[str, Any]:
        """Run a single sample for a model across all evaluations."""
        sample_results = {
            "sample_id": sample_id,
            "model_config": model_config,
            "evaluation_results": {},
            "aggregated_metrics": {}
        }
        
        total_score = 0
        total_max_score = 0
        total_tokens = 0
        total_latency = 0
        total_tasks = 0
        
        for eval_name in evaluations:
            try:
                # Run evaluation
                eval_result = evaluation_loader.run_evaluation(eval_name, model_config)
                
                # Extract key metrics
                summary = eval_result.get("summary", {})
                
                sample_results["evaluation_results"][eval_name] = {
                    "score": summary.get("total_score", 0),
                    "max_score": summary.get("max_score", 1),
                    "pass_rate": summary.get("pass_rate", 0),
                    "tokens": summary.get("total_tokens", 0),
                    "latency_s": summary.get("avg_latency_s", 0),
                    "tasks": summary.get("total_tasks", 0)
                }
                
                # Accumulate for aggregation
                total_score += summary.get("total_score", 0)
                total_max_score += summary.get("max_score", 1)
                total_tokens += summary.get("total_tokens", 0)
                total_latency += summary.get("avg_latency_s", 0)
                total_tasks += summary.get("total_tasks", 0)
                
            except Exception as e:
                print(f"Error running evaluation {eval_name}: {e}")
                sample_results["evaluation_results"][eval_name] = {
                    "error": str(e),
                    "score": 0,
                    "max_score": 1,
                    "pass_rate": 0,
                    "tokens": 0,
                    "latency_s": 0,
                    "tasks": 0
                }
        
        # Calculate aggregated metrics
        num_evals = len(evaluations)
        sample_results["aggregated_metrics"] = {
            "total_score": total_score,
            "total_max_score": total_max_score,
            "overall_score_percentage": (total_score / total_max_score * 100) if total_max_score > 0 else 0,
            "total_tokens": total_tokens,
            "avg_latency_s": round(total_latency / num_evals, 2) if num_evals > 0 else 0,
            "total_tasks": total_tasks
        }
        
        return sample_results
    
    def _analyze_results(self, model_a_results: List[Dict[str, Any]], 
                        model_b_results: List[Dict[str, Any]],
                        confidence_level: float) -> Dict[str, Any]:
        """Perform statistical analysis on A/B test results."""
        # Extract key metrics for analysis
        a_scores = [r["aggregated_metrics"]["overall_score_percentage"] for r in model_a_results]
        b_scores = [r["aggregated_metrics"]["overall_score_percentage"] for r in model_b_results]
        
        a_tokens = [r["aggregated_metrics"]["total_tokens"] for r in model_a_results]
        b_tokens = [r["aggregated_metrics"]["total_tokens"] for r in model_b_results]
        
        a_latency = [r["aggregated_metrics"]["avg_latency_s"] for r in model_a_results]
        b_latency = [r["aggregated_metrics"]["avg_latency_s"] for r in model_b_results]
        
        analysis = {
            "sample_size": len(model_a_results),
            "confidence_level": confidence_level,
            "metrics": {}
        }
        
        # Analyze each metric
        for metric_name, a_values, b_values in [
            ("score_percentage", a_scores, b_scores),
            ("tokens", a_tokens, b_tokens),
            ("latency_s", a_latency, b_latency)
        ]:
            metric_analysis = self._analyze_metric(a_values, b_values, confidence_level)
            analysis["metrics"][metric_name] = metric_analysis
        
        return analysis
    
    def _analyze_metric(self, a_values: List[float], b_values: List[float], 
                       confidence_level: float) -> Dict[str, Any]:
        """Analyze a specific metric statistically."""
        if not a_values or not b_values:
            return {"error": "Insufficient data"}
        
        # Basic statistics
        a_mean = mean(a_values)
        b_mean = mean(b_values)
        a_std = stdev(a_values) if len(a_values) > 1 else 0
        b_std = stdev(b_values) if len(b_values) > 1 else 0
        
        # Effect size (difference in means)
        effect_size = b_mean - a_mean
        percent_change = (effect_size / a_mean * 100) if a_mean != 0 else 0
        
        # Statistical significance test (two-sample t-test)
        try:
            t_stat, p_value = stats.ttest_ind(a_values, b_values)
            alpha = 1 - confidence_level
            significant = p_value < alpha
        except Exception:
            t_stat, p_value, significant = None, None, False
        
        # Confidence interval for the difference
        try:
            diff_std = (a_std**2 / len(a_values) + b_std**2 / len(b_values))**0.5
            t_critical = stats.t.ppf((1 + confidence_level) / 2, len(a_values) + len(b_values) - 2)
            margin_error = t_critical * diff_std
            ci_lower = effect_size - margin_error
            ci_upper = effect_size + margin_error
        except Exception:
            ci_lower, ci_upper = None, None
        
        return {
            "model_a": {
                "mean": round(a_mean, 4),
                "std": round(a_std, 4),
                "min": min(a_values),
                "max": max(a_values)
            },
            "model_b": {
                "mean": round(b_mean, 4),
                "std": round(b_std, 4),
                "min": min(b_values),
                "max": max(b_values)
            },
            "comparison": {
                "effect_size": round(effect_size, 4),
                "percent_change": round(percent_change, 2),
                "t_statistic": round(t_stat, 4) if t_stat else None,
                "p_value": round(p_value, 6) if p_value else None,
                "significant": significant,
                "confidence_interval": {
                    "lower": round(ci_lower, 4) if ci_lower else None,
                    "upper": round(ci_upper, 4) if ci_upper else None
                }
            }
        }
    
    def _generate_conclusion(self, analysis: Dict[str, Any], config: ABTestConfig) -> str:
        """Generate human-readable conclusion from statistical analysis."""
        conclusions = []
        
        model_a_name = config.model_a.get("model_name", "Model A")
        model_b_name = config.model_b.get("model_name", "Model B")
        
        for metric_name, metric_data in analysis["metrics"].items():
            if "error" in metric_data:
                continue
            
            comparison = metric_data["comparison"]
            effect_size = comparison["effect_size"]
            percent_change = comparison["percent_change"]
            significant = comparison["significant"]
            
            if significant:
                direction = "better" if effect_size > 0 else "worse"
                conclusions.append(
                    f"{model_b_name} performs significantly {direction} than {model_a_name} "
                    f"on {metric_name} ({percent_change:+.1f}% change)"
                )
            else:
                conclusions.append(
                    f"No significant difference between {model_a_name} and {model_b_name} "
                    f"on {metric_name} ({percent_change:+.1f}% change, not significant)"
                )
        
        if not conclusions:
            return "Insufficient data for statistical conclusions"
        
        return "; ".join(conclusions)
    
    def _save_results(self, result: ABTestResult):
        """Save A/B test results to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ab_test_{result.config.name}_{timestamp}.json"
        filepath = self.results_dir / filename
        
        # Convert to serializable format
        result_dict = asdict(result)
        
        with open(filepath, 'w') as f:
            json.dump(result_dict, f, indent=2)
        
        print(f"A/B test results saved to: {filepath}")
    
    def load_results(self, filepath: str) -> ABTestResult:
        """Load A/B test results from file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Reconstruct ABTestResult object
        config = ABTestConfig(**data["config"])
        
        return ABTestResult(
            config=config,
            model_a_results=data["model_a_results"],
            model_b_results=data["model_b_results"],
            statistical_analysis=data["statistical_analysis"],
            conclusion=data["conclusion"],
            timestamp=data["timestamp"],
            duration_s=data["duration_s"]
        )
    
    def list_saved_results(self) -> List[str]:
        """List all saved A/B test result files."""
        return [str(f) for f in self.results_dir.glob("ab_test_*.json")]
    
    def compare_multiple_models(self, models: List[Dict[str, Any]], 
                               evaluations: List[str],
                               evaluation_loader: Any,
                               sample_size: int = 50) -> Dict[str, Any]:
        """Compare multiple models pairwise using A/B tests."""
        results = {
            "models": models,
            "evaluations": evaluations,
            "pairwise_tests": {},
            "rankings": {}
        }
        
        # Run pairwise A/B tests
        for i, model_a in enumerate(models):
            for j, model_b in enumerate(models[i+1:], i+1):
                test_name = f"model_{i}_vs_model_{j}"
                
                config = ABTestConfig(
                    name=test_name,
                    description=f"Compare {model_a.get('model_name')} vs {model_b.get('model_name')}",
                    model_a=model_a,
                    model_b=model_b,
                    evaluations=evaluations,
                    sample_size=sample_size
                )
                
                test_result = self.run_ab_test(config, evaluation_loader)
                results["pairwise_tests"][test_name] = test_result
        
        # Generate overall rankings
        results["rankings"] = self._generate_rankings(results["pairwise_tests"])
        
        return results
    
    def _generate_rankings(self, pairwise_tests: Dict[str, ABTestResult]) -> Dict[str, Any]:
        """Generate overall model rankings from pairwise test results."""
        # This is a simplified ranking based on win/loss counts
        # More sophisticated methods could be implemented (ELO, Bradley-Terry, etc.)
        
        model_wins = {}
        model_names = set()
        
        for test_result in pairwise_tests.values():
            model_a_name = test_result.config.model_a.get("model_name")
            model_b_name = test_result.config.model_b.get("model_name")
            
            model_names.add(model_a_name)
            model_names.add(model_b_name)
            
            if model_a_name not in model_wins:
                model_wins[model_a_name] = 0
            if model_b_name not in model_wins:
                model_wins[model_b_name] = 0
            
            # Determine winner based on score percentage
            score_analysis = test_result.statistical_analysis["metrics"]["score_percentage"]
            if score_analysis["comparison"]["significant"]:
                if score_analysis["comparison"]["effect_size"] > 0:
                    model_wins[model_b_name] += 1
                else:
                    model_wins[model_a_name] += 1
            # No winner for non-significant differences
        
        # Sort by wins
        ranked_models = sorted(model_wins.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "ranking": ranked_models,
            "win_counts": model_wins
        }


# Example usage and configuration templates
def create_ab_test_config_template(name: str, output_path: str):
    """Create an A/B test configuration template."""
    template = {
        "name": name,
        "description": f"A/B test comparing two models on {name}",
        "model_a": {
            "model_name": "gpt-4o-mini",
            "provider": "openai",
            "api_key": "${OPENAI_API_KEY}",
            "max_tokens": 4096,
            "temperature": 0.0
        },
        "model_b": {
            "model_name": "claude-3-5-haiku-20241022",
            "provider": "anthropic", 
            "api_key": "${ANTHROPIC_API_KEY}",
            "max_tokens": 4096,
            "temperature": 0.0
        },
        "evaluations": [
            "tool_calling_micro",
            "single_file_fix"
        ],
        "sample_size": 50,
        "confidence_level": 0.95,
        "randomization_seed": 42,
        "metadata": {
            "author": "Your Name",
            "purpose": "Model comparison",
            "created": datetime.now().isoformat()
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(template, f, indent=2)
    
    print(f"Created A/B test config template: {output_path}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="A/B testing framework")
    parser.add_argument("--create-config", help="Create A/B test config template")
    parser.add_argument("--output", help="Output path for template")
    parser.add_argument("--run-config", help="Run A/B test from config file")
    parser.add_argument("--list-results", action="store_true", help="List saved results")
    
    args = parser.parse_args()
    
    if args.create_config:
        output_path = args.output or f"ab_test_{args.create_config}.json"
        create_ab_test_config_template(args.create_config, output_path)
    elif args.list_results:
        framework = ABTestFramework()
        results = framework.list_saved_results()
        print("Saved A/B test results:")
        for result_file in results:
            print(f"  - {result_file}")
    elif args.run_config:
        print(f"Running A/B test from config: {args.run_config}")
        # Implementation would load config and run test
