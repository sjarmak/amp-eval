#!/usr/bin/env python3
"""
Graders package for custom evaluation plugins.
"""

from .base import (
    BaseGrader,
    GraderConfig,
    GradeResult,
    GraderType,
    GraderFactory,
    CompositeGrader
)

from .plugin_loader import GraderPluginLoader, create_grader_template

# Import built-in graders to register them
from .builtin import (
    ExactMatchGrader,
    ContainsGrader,
    RegexGrader,
    FunctionGrader
)

__all__ = [
    "BaseGrader",
    "GraderConfig",
    "GradeResult", 
    "GraderType",
    "GraderFactory",
    "CompositeGrader",
    "GraderPluginLoader",
    "create_grader_template",
    "ExactMatchGrader",
    "ContainsGrader",
    "RegexGrader", 
    "FunctionGrader"
]
