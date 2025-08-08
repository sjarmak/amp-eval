# Phase 7: Extensibility Implementation

This document describes the implementation of Phase 7 extensibility features for the Amp Model-Efficacy Evaluation Suite, providing a comprehensive plugin architecture for models, graders, and evaluation components.

## 🏗️ Architecture Overview

The Phase 7 implementation introduces six major extensibility components:

1. **BaseModelRunner Interface** - Unified interface for different model providers
2. **Custom Grader Plugin System** - Pluggable evaluation logic
3. **Dynamic Evaluation Loading** - Runtime evaluation discovery and execution
4. **A/B Testing Framework** - Statistical model comparison
5. **Custom Metric Definitions** - Flexible performance measurement
6. **Evaluation Suite Versioning** - Version management and compatibility

## 📁 Directory Structure

```
src/amp_eval/
├── models/                    # Model runner interfaces
│   ├── __init__.py
│   ├── base.py               # BaseModelRunner interface
│   ├── openai_runner.py      # OpenAI implementation
│   ├── anthropic_runner.py   # Anthropic implementation
│   └── local_runner.py       # Local GGUF implementation
├── graders/                   # Custom grader system
│   ├── __init__.py
│   ├── base.py               # BaseGrader interface
│   ├── builtin.py            # Built-in grader implementations
│   └── plugin_loader.py      # Dynamic grader loading
├── evaluation/                # Dynamic evaluation system
│   └── dynamic_loader.py     # Evaluation discovery and execution
├── testing/                   # A/B testing framework
│   └── ab_framework.py       # Statistical model comparison
├── metrics/                   # Custom metrics system
│   └── custom_metrics.py     # Metric definitions and calculation
├── versioning/                # Version management
│   └── version_manager.py    # Evaluation versioning
└── __init__.py               # Package exports
```

## 🔌 1. BaseModelRunner Interface

### Purpose
Unified interface for integrating different model providers (OpenAI, Anthropic, local models) with consistent API and behavior.

### Key Components

**ModelProvider Enum**
```python
class ModelProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL_GGUF = "local_gguf"
    CUSTOM = "custom"
```

**ModelConfig Dataclass**
```python
@dataclass
class ModelConfig:
    name: str
    provider: ModelProvider
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_id: str = ""
    max_tokens: int = 4096
    temperature: float = 0.0
    timeout: int = 300
    extra_params: Dict[str, Any] = None
```

**BaseModelRunner Interface**
```python
class BaseModelRunner(ABC):
    @abstractmethod
    def initialize(self) -> bool: pass
    
    @abstractmethod
    def run(self, prompt: str, **kwargs) -> ModelResponse: pass
    
    @abstractmethod
    def estimate_tokens(self, text: str) -> int: pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]: pass
```

### Usage Example

```python
from amp_eval import ModelConfig, ModelProvider, ModelRunnerFactory

# Create OpenAI runner
config = ModelConfig(
    name="gpt-4o",
    provider=ModelProvider.OPENAI,
    model_id="gpt-4o",
    api_key="your-api-key"
)

runner = ModelRunnerFactory.create_runner(config)
runner.initialize()

response = runner.run("Write a Python function to add two numbers")
print(f"Response: {response.content}")
print(f"Tokens used: {response.tokens_used}")
```

## 🎯 2. Custom Grader Plugin System

### Purpose
Pluggable evaluation logic allowing custom grading criteria for different types of tasks.

### Built-in Grader Types

- **ExactMatchGrader** - Exact string matching
- **ContainsGrader** - Substring matching
- **RegexGrader** - Regular expression matching
- **FunctionGrader** - Custom function evaluation

### Custom Grader Development

Place a `grader.py` file next to your evaluation YAML:

```python
from amp_eval.graders import BaseGrader, GraderConfig, GradeResult

class CustomCodeGrader(BaseGrader):
    def grade(self, response: str, expected: Any = None, context: Dict[str, Any] = None) -> GradeResult:
        # Custom grading logic
        keywords = ["def", "return"]
        found = sum(1 for k in keywords if k in response)
        score = found / len(keywords)
        
        return GradeResult(
            score=score,
            max_score=1.0,
            passed=score >= self.config.pass_threshold,
            feedback=f"Found {found}/{len(keywords)} required keywords"
        )

def create_grader() -> BaseGrader:
    config = GraderConfig(name="custom_code", grader_type=GraderType.CUSTOM)
    return CustomCodeGrader(config)
```

### Usage Example

```python
from amp_eval.graders import GraderPluginLoader

loader = GraderPluginLoader()
grader = loader.load_grader_for_evaluation("evals/coding_task.yaml")

result = grader.grade("def add(a, b): return a + b", "function")
print(f"Grade: {result.score:.2f}, Passed: {result.passed}")
```

## 🔄 3. Dynamic Evaluation Loading

### Purpose
Runtime discovery and execution of evaluation suites with automatic model routing and custom grader integration.

### Evaluation Specification Format

```yaml
name: "coding_fundamentals"
description: "Basic coding task evaluation"
version: "1.0"
metadata:
  author: "Your Name"
  difficulty: "beginner"
grading:
  type: "custom"
  pass_threshold: 0.7
tasks:
  - name: "addition_function"
    prompt: "Write a Python function that adds two numbers"
    expected: "def add"
    metadata:
      category: "functions"
  - name: "loop_example"
    prompt: "Write a for loop that prints numbers 1-5"
    expected: "for"
    metadata:
      category: "loops"
```

### Usage Example

```python
from amp_eval import DynamicEvaluationLoader

loader = DynamicEvaluationLoader("evals")

# Discover evaluations
evaluations = loader.load_all_evaluations()

# Run evaluation with specific model
model_config = {
    "model_name": "gpt-4o-mini",
    "provider": "openai",
    "api_key": "your-key"
}

results = loader.run_evaluation("coding_fundamentals", model_config)
print(f"Pass rate: {results['summary']['pass_rate']:.2%}")
```

## 📊 4. A/B Testing Framework

### Purpose
Statistical comparison of model performance with confidence intervals and significance testing.

### Test Configuration

```python
from amp_eval import ABTestConfig, ABTestFramework

config = ABTestConfig(
    name="gpt_vs_claude",
    description="Compare GPT-4o vs Claude-3.5 on coding tasks",
    model_a={
        "model_name": "gpt-4o",
        "provider": "openai"
    },
    model_b={
        "model_name": "claude-3-5-sonnet-20241022",
        "provider": "anthropic"
    },
    evaluations=["coding_fundamentals", "tool_calling_micro"],
    sample_size=100,
    confidence_level=0.95
)

framework = ABTestFramework()
result = framework.run_ab_test(config, evaluation_loader)
```

### Statistical Analysis

The framework provides:
- **Two-sample t-tests** for significance
- **Confidence intervals** for effect sizes
- **Effect size calculations** (Cohen's d)
- **Multiple metric comparison** (accuracy, latency, cost)

### Results Format

```python
{
    "statistical_analysis": {
        "metrics": {
            "score_percentage": {
                "model_a": {"mean": 87.5, "std": 12.3},
                "model_b": {"mean": 91.2, "std": 10.8},
                "comparison": {
                    "effect_size": 3.7,
                    "p_value": 0.023,
                    "significant": true,
                    "confidence_interval": {"lower": 0.5, "upper": 6.9}
                }
            }
        }
    },
    "conclusion": "Model B performs significantly better..."
}
```

## 📈 5. Custom Metrics System

### Purpose
Flexible performance measurement beyond basic accuracy, including cost, latency, quality, and efficiency metrics.

### Built-in Metric Types

- **AccuracyMetric** - Task completion accuracy
- **LatencyMetric** - Response time measurement
- **CostMetric** - Token-based cost calculation
- **QualityMetric** - Response quality assessment
- **EfficiencyMetric** - Accuracy per unit cost/time

### Custom Metric Definition

```python
from amp_eval import MetricDefinition, MetricType, MetricCalculator

# Define custom metric
complexity_def = MetricDefinition(
    name="code_complexity",
    metric_type=MetricType.CUSTOM,
    description="Code complexity in responses",
    unit="ratio",
    higher_is_better=False,
    parameters={"complexity_threshold": 10}
)

# Custom calculation function
def calculate_complexity(data: Dict[str, Any], parameters: Dict[str, Any]) -> float:
    # Analyze code complexity in responses
    total_complexity = 0
    for task in data["task_results"]:
        response = task["response"]
        complexity = len([line for line in response.split('\n') 
                         if any(kw in line for kw in ['if', 'for', 'while'])])
        total_complexity += complexity
    return total_complexity / len(data["task_results"])

# Register metric
calculator = MetricCalculator()
calculator.register_custom_function_metric(complexity_def, calculate_complexity)
```

### Usage Example

```python
# Calculate all metrics for evaluation results
results = calculator.calculate_all_metrics(evaluation_data)

for metric_name, result in results.items():
    print(f"{metric_name}: {result.value:.4f} {result.unit}")

# Get aggregated score
aggregate_score = calculator.aggregate_metrics(results)
print(f"Overall Score: {aggregate_score:.4f}")
```

## 🏷️ 6. Evaluation Suite Versioning

### Purpose
Version management for evaluation suites with semantic versioning, compatibility checking, and migration support.

### Version Creation

```python
from amp_eval import VersionManager

manager = VersionManager()

# Create new version
version = manager.create_version(
    eval_name="coding_fundamentals",
    version="2.0.0",
    description="Added new coding challenges and updated grading",
    author="Your Name"
)
```

### Compatibility Checking

```python
# Check version compatibility
compatibility = manager.check_compatibility("coding_fundamentals", "1.0.0", "2.0.0")

if compatibility.compatible:
    print("Versions are compatible")
    if compatibility.migration_required:
        print("Migration recommended")
else:
    print("Breaking changes detected")
```

### Version Resolution

```python
# Load specific version
eval_data, resolved_version = manager.load_versioned_evaluation(
    "coding_fundamentals", 
    "^1.0.0"  # Compatible with 1.x.x
)

# Get latest version
latest = manager.get_latest_version("coding_fundamentals")
```

## 🚀 Quick Start

### 1. Installation

```bash
# Install dependencies
pip install pydantic loguru tiktoken anthropic openai scipy semantic-version

# Add to Python path
export PYTHONPATH="${PYTHONPATH}:/path/to/amp-eval/src"
```

### 2. Run Demo

```bash
cd amp-eval
python examples/phase7_demo.py
```

### 3. Create Custom Grader

```bash
cd evals
python -m amp_eval.graders.plugin_loader --create-template my_evaluation --output grader.py
```

### 4. Create Evaluation Template

```bash
python -m amp_eval.evaluation.dynamic_loader --create-template my_evaluation --output my_evaluation.yaml
```

## 🔧 Integration with Existing System

The Phase 7 extensibility features integrate with the existing amp_runner.py:

```python
# In amp_runner.py - enhanced with new model runners
from amp_eval import ModelRunnerFactory, ModelConfig, ModelProvider

class AmpRunner:
    def __init__(self, config_path: str = "config/agent_settings.yaml"):
        self.config = self._load_config()
        self.model_runners = {}  # Cache for model runners
    
    def get_model_runner(self, model: str) -> BaseModelRunner:
        if model not in self.model_runners:
            # Determine provider and create config
            if "gpt" in model:
                provider = ModelProvider.OPENAI
            elif "claude" in model:
                provider = ModelProvider.ANTHROPIC
            else:
                provider = ModelProvider.LOCAL_GGUF
            
            config = ModelConfig(
                name=model,
                provider=provider,
                model_id=model
            )
            
            runner = ModelRunnerFactory.create_runner(config)
            runner.initialize()
            self.model_runners[model] = runner
        
        return self.model_runners[model]
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Unit tests
python -m pytest tests/test_models.py
python -m pytest tests/test_graders.py
python -m pytest tests/test_evaluation.py

# Integration tests
python -m pytest tests/test_integration.py

# End-to-end demo
python examples/phase7_demo.py
```

## 📚 Future Extensions

The plugin architecture supports future enhancements:

1. **Additional Model Providers** - Easy integration of new providers
2. **Advanced Grading Logic** - LLM-based graders, multi-stage evaluation
3. **Custom Evaluation Types** - Performance benchmarks, security tests
4. **Enhanced Metrics** - Domain-specific metrics, composite scoring
5. **Version Migration Tools** - Automated evaluation upgrades

## 🎯 Benefits

Phase 7 extensibility provides:

- **Flexibility** - Support for any model provider or evaluation type
- **Maintainability** - Clean interfaces and plugin architecture
- **Scalability** - Easy addition of new components
- **Reliability** - Comprehensive testing and version management
- **Future-Proofing** - Designed for evolving AI landscape

## 📋 Next Steps

With Phase 7 complete, the evaluation suite is ready for:

1. **Phase 8: Governance & Cost Controls** - Financial monitoring and quotas
2. **Phase 9: Documentation & UX** - Developer experience improvements
3. **Phase 10: Launch Strategy** - Organization-wide deployment

The extensible architecture ensures the evaluation platform can evolve with changing model capabilities and evaluation requirements.
