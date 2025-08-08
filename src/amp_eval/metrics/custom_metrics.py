#!/usr/bin/env python3
"""
Custom metric definitions and calculation framework.
"""

import time
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum


class MetricType(Enum):
    """Types of custom metrics."""
    ACCURACY = "accuracy"
    LATENCY = "latency"
    COST = "cost"
    QUALITY = "quality"
    EFFICIENCY = "efficiency"
    ROBUSTNESS = "robustness"
    CUSTOM = "custom"


@dataclass
class MetricDefinition:
    """Definition of a custom metric."""
    name: str
    metric_type: MetricType
    description: str
    unit: str
    higher_is_better: bool
    aggregation_method: str = "mean"  # mean, sum, max, min, median
    weight: float = 1.0
    parameters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


@dataclass
class MetricResult:
    """Result from a metric calculation."""
    metric_name: str
    value: float
    unit: str
    metadata: Dict[str, Any] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.timestamp is None:
            self.timestamp = time.time()


class BaseMetric(ABC):
    """Abstract base class for custom metrics."""
    
    def __init__(self, definition: MetricDefinition):
        self.definition = definition
    
    @abstractmethod
    def calculate(self, data: Dict[str, Any]) -> MetricResult:
        """Calculate the metric value from the given data."""
        pass
    
    @abstractmethod
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate that the data contains required fields."""
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """Get information about this metric."""
        return {
            "name": self.definition.name,
            "type": self.definition.metric_type.value,
            "description": self.definition.description,
            "unit": self.definition.unit,
            "higher_is_better": self.definition.higher_is_better,
            "aggregation_method": self.definition.aggregation_method,
            "parameters": self.definition.parameters
        }


class AccuracyMetric(BaseMetric):
    """Metric for measuring accuracy/correctness."""
    
    def calculate(self, data: Dict[str, Any]) -> MetricResult:
        """Calculate accuracy as ratio of correct responses."""
        if not self.validate_data(data):
            return MetricResult(
                metric_name=self.definition.name,
                value=0.0,
                unit=self.definition.unit,
                metadata={"error": "invalid_data"}
            )
        
        results = data.get("task_results", [])
        if not results:
            return MetricResult(
                metric_name=self.definition.name,
                value=0.0,
                unit=self.definition.unit,
                metadata={"error": "no_results"}
            )
        
        total_score = sum(task.get("grade", {}).get("score", 0) for task in results)
        total_max_score = sum(task.get("grade", {}).get("max_score", 1) for task in results)
        
        accuracy = (total_score / total_max_score) if total_max_score > 0 else 0.0
        
        return MetricResult(
            metric_name=self.definition.name,
            value=accuracy,
            unit=self.definition.unit,
            metadata={
                "total_score": total_score,
                "total_max_score": total_max_score,
                "num_tasks": len(results)
            }
        )
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate data has task results with grades."""
        return "task_results" in data and isinstance(data["task_results"], list)


class LatencyMetric(BaseMetric):
    """Metric for measuring response latency."""
    
    def calculate(self, data: Dict[str, Any]) -> MetricResult:
        """Calculate average response latency."""
        if not self.validate_data(data):
            return MetricResult(
                metric_name=self.definition.name,
                value=0.0,
                unit=self.definition.unit,
                metadata={"error": "invalid_data"}
            )
        
        results = data.get("task_results", [])
        latencies = []
        
        for task in results:
            model_metrics = task.get("model_metrics", {})
            latency = model_metrics.get("latency_s")
            if latency is not None:
                latencies.append(latency)
        
        if not latencies:
            return MetricResult(
                metric_name=self.definition.name,
                value=0.0,
                unit=self.definition.unit,
                metadata={"error": "no_latency_data"}
            )
        
        # Apply aggregation method
        if self.definition.aggregation_method == "mean":
            value = sum(latencies) / len(latencies)
        elif self.definition.aggregation_method == "max":
            value = max(latencies)
        elif self.definition.aggregation_method == "min":
            value = min(latencies)
        elif self.definition.aggregation_method == "median":
            sorted_latencies = sorted(latencies)
            n = len(sorted_latencies)
            value = sorted_latencies[n//2] if n % 2 == 1 else (sorted_latencies[n//2-1] + sorted_latencies[n//2]) / 2
        else:
            value = sum(latencies) / len(latencies)  # Default to mean
        
        return MetricResult(
            metric_name=self.definition.name,
            value=value,
            unit=self.definition.unit,
            metadata={
                "min_latency": min(latencies),
                "max_latency": max(latencies),
                "num_measurements": len(latencies),
                "aggregation_method": self.definition.aggregation_method
            }
        )
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate data has task results with model metrics."""
        return "task_results" in data and isinstance(data["task_results"], list)


class CostMetric(BaseMetric):
    """Metric for measuring token/API cost."""
    
    def calculate(self, data: Dict[str, Any]) -> MetricResult:
        """Calculate total cost based on token usage."""
        if not self.validate_data(data):
            return MetricResult(
                metric_name=self.definition.name,
                value=0.0,
                unit=self.definition.unit,
                metadata={"error": "invalid_data"}
            )
        
        results = data.get("task_results", [])
        total_tokens = 0
        
        for task in results:
            model_metrics = task.get("model_metrics", {})
            tokens = model_metrics.get("tokens_used", 0)
            total_tokens += tokens
        
        # Get cost per token from parameters (or use default)
        cost_per_token = self.definition.parameters.get("cost_per_token", 0.00001)  # Default $0.01 per 1K tokens
        total_cost = total_tokens * cost_per_token
        
        return MetricResult(
            metric_name=self.definition.name,
            value=total_cost,
            unit=self.definition.unit,
            metadata={
                "total_tokens": total_tokens,
                "cost_per_token": cost_per_token,
                "num_tasks": len(results)
            }
        )
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate data has task results with model metrics."""
        return "task_results" in data and isinstance(data["task_results"], list)


class QualityMetric(BaseMetric):
    """Metric for measuring response quality."""
    
    def calculate(self, data: Dict[str, Any]) -> MetricResult:
        """Calculate quality score based on multiple factors."""
        if not self.validate_data(data):
            return MetricResult(
                metric_name=self.definition.name,
                value=0.0,
                unit=self.definition.unit,
                metadata={"error": "invalid_data"}
            )
        
        results = data.get("task_results", [])
        quality_factors = []
        
        for task in results:
            grade = task.get("grade", {})
            
            # Base score
            base_score = grade.get("score", 0) / grade.get("max_score", 1)
            
            # Quality adjustments based on response characteristics
            response = task.get("response", "")
            
            # Length penalty/bonus
            length_factor = 1.0
            min_length = self.definition.parameters.get("min_response_length", 10)
            max_length = self.definition.parameters.get("max_response_length", 1000)
            
            if len(response) < min_length:
                length_factor = 0.5  # Penalty for too short
            elif len(response) > max_length:
                length_factor = 0.8  # Penalty for too verbose
            
            # Coherence bonus (simple heuristic)
            coherence_factor = 1.0
            if response:
                # Check for proper sentence structure
                sentences = response.split('.')
                if len(sentences) > 1:
                    coherence_factor = 1.1  # Bonus for multi-sentence responses
            
            quality_score = base_score * length_factor * coherence_factor
            quality_factors.append(min(quality_score, 1.0))  # Cap at 1.0
        
        if not quality_factors:
            return MetricResult(
                metric_name=self.definition.name,
                value=0.0,
                unit=self.definition.unit,
                metadata={"error": "no_quality_data"}
            )
        
        average_quality = sum(quality_factors) / len(quality_factors)
        
        return MetricResult(
            metric_name=self.definition.name,
            value=average_quality,
            unit=self.definition.unit,
            metadata={
                "min_quality": min(quality_factors),
                "max_quality": max(quality_factors),
                "num_tasks": len(quality_factors)
            }
        )
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate data has task results with responses."""
        return "task_results" in data and isinstance(data["task_results"], list)


class EfficiencyMetric(BaseMetric):
    """Metric for measuring efficiency (accuracy per unit cost/time)."""
    
    def calculate(self, data: Dict[str, Any]) -> MetricResult:
        """Calculate efficiency as accuracy divided by resource usage."""
        if not self.validate_data(data):
            return MetricResult(
                metric_name=self.definition.name,
                value=0.0,
                unit=self.definition.unit,
                metadata={"error": "invalid_data"}
            )
        
        # Calculate accuracy
        accuracy_metric = AccuracyMetric(MetricDefinition(
            name="temp_accuracy",
            metric_type=MetricType.ACCURACY,
            description="Temporary accuracy",
            unit="ratio",
            higher_is_better=True
        ))
        accuracy_result = accuracy_metric.calculate(data)
        accuracy = accuracy_result.value
        
        # Calculate resource usage based on efficiency type
        efficiency_type = self.definition.parameters.get("efficiency_type", "cost")
        
        if efficiency_type == "cost":
            cost_metric = CostMetric(MetricDefinition(
                name="temp_cost",
                metric_type=MetricType.COST,
                description="Temporary cost",
                unit="USD",
                higher_is_better=False,
                parameters=self.definition.parameters
            ))
            cost_result = cost_metric.calculate(data)
            resource_usage = cost_result.value
        elif efficiency_type == "time":
            latency_metric = LatencyMetric(MetricDefinition(
                name="temp_latency",
                metric_type=MetricType.LATENCY,
                description="Temporary latency",
                unit="seconds",
                higher_is_better=False
            ))
            latency_result = latency_metric.calculate(data)
            resource_usage = latency_result.value
        else:
            return MetricResult(
                metric_name=self.definition.name,
                value=0.0,
                unit=self.definition.unit,
                metadata={"error": f"unknown_efficiency_type: {efficiency_type}"}
            )
        
        # Calculate efficiency
        efficiency = accuracy / resource_usage if resource_usage > 0 else 0.0
        
        return MetricResult(
            metric_name=self.definition.name,
            value=efficiency,
            unit=self.definition.unit,
            metadata={
                "accuracy": accuracy,
                "resource_usage": resource_usage,
                "efficiency_type": efficiency_type
            }
        )
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate data has task results."""
        return "task_results" in data and isinstance(data["task_results"], list)


class CustomFunctionMetric(BaseMetric):
    """Metric that uses a custom function for calculation."""
    
    def __init__(self, definition: MetricDefinition, calculation_function: Callable):
        super().__init__(definition)
        self.calculation_function = calculation_function
    
    def calculate(self, data: Dict[str, Any]) -> MetricResult:
        """Calculate using the custom function."""
        try:
            value = self.calculation_function(data, self.definition.parameters)
            return MetricResult(
                metric_name=self.definition.name,
                value=float(value),
                unit=self.definition.unit,
                metadata={"custom_function": True}
            )
        except Exception as e:
            return MetricResult(
                metric_name=self.definition.name,
                value=0.0,
                unit=self.definition.unit,
                metadata={"error": str(e), "custom_function": True}
            )
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validation is delegated to the custom function."""
        return True


class MetricCalculator:
    """Calculator for managing and computing multiple metrics."""
    
    def __init__(self):
        self.metrics = {}
        self.metric_factories = {
            MetricType.ACCURACY: AccuracyMetric,
            MetricType.LATENCY: LatencyMetric,
            MetricType.COST: CostMetric,
            MetricType.QUALITY: QualityMetric,
            MetricType.EFFICIENCY: EfficiencyMetric
        }
    
    def register_metric(self, metric: BaseMetric):
        """Register a metric for calculation."""
        self.metrics[metric.definition.name] = metric
    
    def register_metric_definition(self, definition: MetricDefinition) -> BaseMetric:
        """Register a metric from definition."""
        if definition.metric_type in self.metric_factories:
            metric = self.metric_factories[definition.metric_type](definition)
            self.register_metric(metric)
            return metric
        else:
            raise ValueError(f"No factory for metric type: {definition.metric_type}")
    
    def register_custom_function_metric(self, definition: MetricDefinition, 
                                      calculation_function: Callable) -> BaseMetric:
        """Register a custom function-based metric."""
        metric = CustomFunctionMetric(definition, calculation_function)
        self.register_metric(metric)
        return metric
    
    def calculate_all_metrics(self, data: Dict[str, Any]) -> Dict[str, MetricResult]:
        """Calculate all registered metrics for the given data."""
        results = {}
        
        for metric_name, metric in self.metrics.items():
            try:
                result = metric.calculate(data)
                results[metric_name] = result
            except Exception as e:
                results[metric_name] = MetricResult(
                    metric_name=metric_name,
                    value=0.0,
                    unit=metric.definition.unit,
                    metadata={"error": str(e)}
                )
        
        return results
    
    def calculate_metric(self, metric_name: str, data: Dict[str, Any]) -> MetricResult:
        """Calculate a specific metric."""
        if metric_name not in self.metrics:
            raise ValueError(f"Metric not registered: {metric_name}")
        
        return self.metrics[metric_name].calculate(data)
    
    def get_metric_info(self, metric_name: str) -> Dict[str, Any]:
        """Get information about a specific metric."""
        if metric_name not in self.metrics:
            raise ValueError(f"Metric not registered: {metric_name}")
        
        return self.metrics[metric_name].get_info()
    
    def list_metrics(self) -> List[str]:
        """List all registered metric names."""
        return list(self.metrics.keys())
    
    def aggregate_metrics(self, metric_results: Dict[str, MetricResult], 
                         weights: Optional[Dict[str, float]] = None) -> float:
        """Aggregate multiple metrics into a single score."""
        if not metric_results:
            return 0.0
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for metric_name, result in metric_results.items():
            metric = self.metrics.get(metric_name)
            if not metric:
                continue
            
            # Get weight
            weight = 1.0
            if weights and metric_name in weights:
                weight = weights[metric_name]
            elif metric:
                weight = metric.definition.weight
            
            # Normalize value (0-1 scale)
            value = result.value
            if not metric.definition.higher_is_better:
                # For metrics where lower is better, invert
                value = 1.0 / (1.0 + value) if value > 0 else 1.0
            
            weighted_sum += value * weight
            total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0


# Example custom metric functions
def code_complexity_metric(data: Dict[str, Any], parameters: Dict[str, Any]) -> float:
    """Custom metric to measure code complexity in responses."""
    results = data.get("task_results", [])
    complexity_scores = []
    
    for task in results:
        response = task.get("response", "")
        
        # Simple complexity heuristics
        lines = response.split('\n')
        complexity = 0
        
        # Count control structures
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ['if', 'for', 'while', 'try', 'except']):
                complexity += 1
        
        # Normalize by response length
        normalized_complexity = complexity / max(len(lines), 1)
        complexity_scores.append(normalized_complexity)
    
    return sum(complexity_scores) / len(complexity_scores) if complexity_scores else 0.0


def error_rate_metric(data: Dict[str, Any], parameters: Dict[str, Any]) -> float:
    """Custom metric to measure error rate in responses."""
    results = data.get("task_results", [])
    if not results:
        return 1.0  # High error rate if no results
    
    error_count = 0
    for task in results:
        # Check for various error indicators
        response = task.get("response", "")
        grade = task.get("grade", {})
        
        # Failed grade
        if not grade.get("passed", False):
            error_count += 1
        
        # Error keywords in response
        error_keywords = parameters.get("error_keywords", ["error", "exception", "failed", "invalid"])
        if any(keyword in response.lower() for keyword in error_keywords):
            error_count += 1
    
    return error_count / len(results)


if __name__ == "__main__":
    # Example usage
    calculator = MetricCalculator()
    
    # Register built-in metrics
    accuracy_def = MetricDefinition(
        name="accuracy",
        metric_type=MetricType.ACCURACY,
        description="Task completion accuracy",
        unit="ratio",
        higher_is_better=True
    )
    calculator.register_metric_definition(accuracy_def)
    
    # Register custom function metric
    complexity_def = MetricDefinition(
        name="code_complexity",
        metric_type=MetricType.CUSTOM,
        description="Code complexity in responses",
        unit="ratio",
        higher_is_better=False
    )
    calculator.register_custom_function_metric(complexity_def, code_complexity_metric)
    
    # Example data
    sample_data = {
        "task_results": [
            {
                "grade": {"score": 1.0, "max_score": 1.0, "passed": True},
                "response": "def add(a, b):\n    return a + b",
                "model_metrics": {"tokens_used": 50, "latency_s": 0.5}
            }
        ]
    }
    
    # Calculate metrics
    results = calculator.calculate_all_metrics(sample_data)
    
    print("Metric Results:")
    for metric_name, result in results.items():
        print(f"{metric_name}: {result.value} {result.unit}")
