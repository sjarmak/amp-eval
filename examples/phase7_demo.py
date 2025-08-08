#!/usr/bin/env python3
"""
Demo script showcasing Phase 7 extensibility features.
"""

import sys
import os

# Add src to path for local imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from amp_eval import (
    ModelConfig, ModelProvider, ModelRunnerFactory,
    GraderConfig, GraderType, GraderFactory,
    DynamicEvaluationLoader,
    ABTestFramework, ABTestConfig,
    MetricCalculator, MetricDefinition, MetricType,
    VersionManager
)

def demo_model_runners():
    """Demonstrate the BaseModelRunner interface."""
    print("=== Model Runner Demo ===")
    
    # OpenAI Runner
    openai_config = ModelConfig(
        name="gpt-4o-mini",
        provider=ModelProvider.OPENAI,
        model_id="gpt-4o-mini",
        api_key=os.getenv("OPENAI_API_KEY", "demo-key"),
        max_tokens=100,
        temperature=0.0
    )
    
    # Anthropic Runner  
    anthropic_config = ModelConfig(
        name="claude-haiku",
        provider=ModelProvider.ANTHROPIC,
        model_id="claude-3-5-haiku-20241022",
        api_key=os.getenv("ANTHROPIC_API_KEY", "demo-key"),
        max_tokens=100,
        temperature=0.0
    )
    
    # Local GGUF Runner
    local_config = ModelConfig(
        name="local-llama",
        provider=ModelProvider.LOCAL_GGUF,
        model_id="llama-3.2-3b",
        base_url="http://localhost:8080",
        max_tokens=100
    )
    
    print(f"Available providers: {ModelRunnerFactory.list_providers()}")
    
    for config in [openai_config, anthropic_config, local_config]:
        try:
            runner = ModelRunnerFactory.create_runner(config)
            print(f"Created runner for {config.name}: {type(runner).__name__}")
            print(f"  Model info: {runner.get_model_info()}")
        except Exception as e:
            print(f"Failed to create runner for {config.name}: {e}")


def demo_custom_graders():
    """Demonstrate the custom grader system."""
    print("\n=== Custom Grader Demo ===")
    
    # Built-in graders
    exact_match = GraderFactory.create_grader(GraderConfig(
        name="exact_match",
        grader_type=GraderType.EXACT_MATCH,
        pass_threshold=1.0
    ))
    
    contains = GraderFactory.create_grader(GraderConfig(
        name="contains_check", 
        grader_type=GraderType.CONTAINS,
        parameters={"case_sensitive": False}
    ))
    
    regex = GraderFactory.create_grader(GraderConfig(
        name="regex_match",
        grader_type=GraderType.REGEX,
        parameters={"pattern": r"def\s+\w+\(.*\):"}
    ))
    
    function_grader = GraderFactory.create_grader(GraderConfig(
        name="test_runner",
        grader_type=GraderType.FUNCTION,
        parameters={"function": "code_compiles"}
    ))
    
    print(f"Available grader types: {GraderFactory.list_grader_types()}")
    
    # Test graders
    test_response = "def add(a, b):\n    return a + b"
    
    for grader in [exact_match, contains, regex, function_grader]:
        try:
            result = grader.grade(test_response, "function")
            print(f"{grader.config.name}: {result.passed} (score: {result.score:.2f})")
        except Exception as e:
            print(f"{grader.config.name}: Error - {e}")


def demo_dynamic_evaluation():
    """Demonstrate dynamic evaluation loading."""
    print("\n=== Dynamic Evaluation Demo ===")
    
    loader = DynamicEvaluationLoader("evals")
    
    # Discover evaluations
    evaluations = loader.discover_evaluations()
    print(f"Found {len(evaluations)} evaluation files")
    
    # Load all evaluations
    loaded = loader.load_all_evaluations()
    print(f"Loaded evaluations: {list(loaded.keys())}")
    
    # List available models
    models = loader.list_models()
    print(f"Available models: {models}")
    
    # Health check
    health = loader.health_check()
    print(f"Model health status: {health}")


def demo_ab_testing():
    """Demonstrate A/B testing framework."""
    print("\n=== A/B Testing Demo ===")
    
    framework = ABTestFramework("results/demo_ab_tests")
    
    # Create test configuration
    config = ABTestConfig(
        name="demo_comparison",
        description="Demo A/B test between two models",
        model_a={
            "model_name": "gpt-4o-mini",
            "provider": "openai"
        },
        model_b={
            "model_name": "claude-3-5-haiku-20241022", 
            "provider": "anthropic"
        },
        evaluations=["tool_calling_micro"],
        sample_size=5,  # Small sample for demo
        confidence_level=0.95,
        randomization_seed=42
    )
    
    print(f"A/B test config: {config.name}")
    print(f"  Model A: {config.model_a['model_name']}")
    print(f"  Model B: {config.model_b['model_name']}")
    print(f"  Sample size: {config.sample_size}")
    
    # List saved results
    saved_results = framework.list_saved_results()
    print(f"Previously saved A/B test results: {len(saved_results)}")


def demo_custom_metrics():
    """Demonstrate custom metrics system."""
    print("\n=== Custom Metrics Demo ===")
    
    calculator = MetricCalculator()
    
    # Register built-in metrics
    accuracy_def = MetricDefinition(
        name="accuracy",
        metric_type=MetricType.ACCURACY,
        description="Task completion accuracy",
        unit="ratio",
        higher_is_better=True
    )
    
    latency_def = MetricDefinition(
        name="avg_latency",
        metric_type=MetricType.LATENCY,
        description="Average response latency",
        unit="seconds",
        higher_is_better=False,
        aggregation_method="mean"
    )
    
    cost_def = MetricDefinition(
        name="total_cost",
        metric_type=MetricType.COST,
        description="Total API cost",
        unit="USD",
        higher_is_better=False,
        parameters={"cost_per_token": 0.00001}
    )
    
    for metric_def in [accuracy_def, latency_def, cost_def]:
        metric = calculator.register_metric_definition(metric_def)
        print(f"Registered metric: {metric.definition.name}")
    
    # Sample data
    sample_data = {
        "task_results": [
            {
                "grade": {"score": 1.0, "max_score": 1.0, "passed": True},
                "response": "def add(a, b):\n    return a + b",
                "model_metrics": {"tokens_used": 50, "latency_s": 0.5}
            },
            {
                "grade": {"score": 0.8, "max_score": 1.0, "passed": True},
                "response": "def multiply(x, y):\n    return x * y",
                "model_metrics": {"tokens_used": 45, "latency_s": 0.3}
            }
        ]
    }
    
    # Calculate metrics
    results = calculator.calculate_all_metrics(sample_data)
    print("\nMetric Results:")
    for name, result in results.items():
        print(f"  {name}: {result.value:.4f} {result.unit}")
    
    # Aggregate score
    aggregate = calculator.aggregate_metrics(results)
    print(f"\nAggregate Score: {aggregate:.4f}")


def demo_versioning():
    """Demonstrate evaluation versioning."""
    print("\n=== Versioning Demo ===")
    
    manager = VersionManager("evals", "demo_versions")
    
    # Demo version operations (without actually creating files)
    print("Version validation examples:")
    
    valid_versions = ["1.0.0", "v2.1.3", "3.0.0-beta.1"]
    invalid_versions = ["not.a.version", "1.x.y"]
    
    for version in valid_versions + invalid_versions:
        valid = manager.validate_version_format(version)
        print(f"  {version}: {'✓' if valid else '✗'}")
    
    # Demo compatibility checking
    print("\nCompatibility examples:")
    
    compatibility_tests = [
        ("1.0.0", "1.0.1"),  # Patch compatible
        ("1.0.0", "1.1.0"),  # Minor compatible
        ("1.0.0", "2.0.0"),  # Major incompatible
    ]
    
    for from_v, to_v in compatibility_tests:
        try:
            # Use dummy evaluation name for demo
            compat = manager.check_compatibility("demo_eval", from_v, to_v)
            status = "✓" if compat.compatible else "✗"
            print(f"  {from_v} → {to_v}: {status} ({compat.migration_notes})")
        except Exception as e:
            print(f"  {from_v} → {to_v}: Error - {e}")


def main():
    """Run all demos."""
    print("🚀 Amp Evaluation Framework - Phase 7 Extensibility Demo")
    print("=" * 60)
    
    try:
        demo_model_runners()
        demo_custom_graders()
        demo_dynamic_evaluation()
        demo_ab_testing()
        demo_custom_metrics()
        demo_versioning()
        
        print("\n" + "=" * 60)
        print("✅ Phase 7 extensibility features demonstrated successfully!")
        print("\nKey Features Implemented:")
        print("• BaseModelRunner interface (OpenAI, Anthropic, Local GGUF)")
        print("• Custom grader plugin system")
        print("• Dynamic evaluation loading")
        print("• A/B testing framework")
        print("• Custom metric definitions")
        print("• Evaluation suite versioning")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
