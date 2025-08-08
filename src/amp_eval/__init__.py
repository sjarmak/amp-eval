#!/usr/bin/env python3
"""
Amp Evaluation Framework - Extensible Plugin Architecture
"""

from .models import (
    BaseModelRunner,
    ModelConfig,
    ModelResponse, 
    ModelProvider,
    ModelRunnerFactory
)

from .graders import (
    BaseGrader,
    GraderConfig,
    GradeResult,
    GraderType,
    GraderFactory,
    GraderPluginLoader
)

from .evaluation.dynamic_loader import (
    DynamicEvaluationLoader,
    EvaluationSpec
)

from .testing.ab_framework import (
    ABTestFramework,
    ABTestConfig,
    ABTestResult
)

from .metrics.custom_metrics import (
    MetricCalculator,
    MetricDefinition,
    MetricResult,
    MetricType
)

from .versioning.version_manager import (
    VersionManager,
    EvaluationVersion,
    VersionStrategy
)

__version__ = "1.0.0"
__author__ = "Amp Evaluation Team"

__all__ = [
    # Models
    "BaseModelRunner",
    "ModelConfig",
    "ModelResponse",
    "ModelProvider", 
    "ModelRunnerFactory",
    
    # Graders
    "BaseGrader",
    "GraderConfig",
    "GradeResult",
    "GraderType",
    "GraderFactory",
    "GraderPluginLoader",
    
    # Evaluation
    "DynamicEvaluationLoader",
    "EvaluationSpec",
    
    # Testing
    "ABTestFramework",
    "ABTestConfig",
    "ABTestResult",
    
    # Metrics
    "MetricCalculator",
    "MetricDefinition",
    "MetricResult",
    "MetricType",
    
    # Versioning
    "VersionManager",
    "EvaluationVersion",
    "VersionStrategy"
]
