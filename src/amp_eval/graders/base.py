#!/usr/bin/env python3
"""
Base grader interface for custom evaluation plugins.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class GraderType(Enum):
    """Types of graders available."""
    EXACT_MATCH = "exact_match"
    CONTAINS = "contains"
    REGEX = "regex"
    FUNCTION = "function"
    LLM_JUDGE = "llm_judge"
    CUSTOM = "custom"


@dataclass
class GradeResult:
    """Result from a grading operation."""
    score: float  # 0.0 to 1.0
    max_score: float  # Maximum possible score
    passed: bool
    feedback: str
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}
    
    @property
    def percentage(self) -> float:
        """Get score as percentage."""
        if self.max_score == 0:
            return 0.0
        return (self.score / self.max_score) * 100


@dataclass
class GraderConfig:
    """Configuration for a grader instance."""
    name: str
    grader_type: GraderType
    weight: float = 1.0
    pass_threshold: float = 0.7
    parameters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}


class BaseGrader(ABC):
    """Abstract base class for all graders."""
    
    def __init__(self, config: GraderConfig):
        self.config = config
    
    @abstractmethod
    def grade(self, response: str, expected: Any = None, context: Dict[str, Any] = None) -> GradeResult:
        """Grade a response and return result."""
        pass
    
    @abstractmethod
    def get_grader_info(self) -> Dict[str, Any]:
        """Return grader information and capabilities."""
        pass
    
    def validate_config(self) -> bool:
        """Validate grader configuration."""
        return True


class CompositeGrader:
    """Grader that combines multiple sub-graders."""
    
    def __init__(self, graders: List[BaseGrader], combination_strategy: str = "weighted_average"):
        self.graders = graders
        self.combination_strategy = combination_strategy
    
    def grade(self, response: str, expected: Any = None, context: Dict[str, Any] = None) -> GradeResult:
        """Grade using all sub-graders and combine results."""
        if not self.graders:
            return GradeResult(
                score=0.0,
                max_score=1.0,
                passed=False,
                feedback="No graders configured",
                details={"error": "empty_graders"}
            )
        
        results = []
        total_weight = 0.0
        
        for grader in self.graders:
            try:
                result = grader.grade(response, expected, context)
                results.append((result, grader.config.weight))
                total_weight += grader.config.weight
            except Exception as e:
                # Log error but continue with other graders
                results.append((
                    GradeResult(
                        score=0.0,
                        max_score=1.0,
                        passed=False,
                        feedback=f"Grader {grader.config.name} failed: {str(e)}",
                        details={"error": str(e)}
                    ),
                    grader.config.weight
                ))
                total_weight += grader.config.weight
        
        return self._combine_results(results, total_weight)
    
    def _combine_results(self, results: List[tuple], total_weight: float) -> GradeResult:
        """Combine grading results using the specified strategy."""
        if self.combination_strategy == "weighted_average":
            return self._weighted_average(results, total_weight)
        elif self.combination_strategy == "all_pass":
            return self._all_pass(results)
        elif self.combination_strategy == "any_pass":
            return self._any_pass(results)
        else:
            raise ValueError(f"Unknown combination strategy: {self.combination_strategy}")
    
    def _weighted_average(self, results: List[tuple], total_weight: float) -> GradeResult:
        """Combine results using weighted average."""
        if total_weight == 0:
            return GradeResult(
                score=0.0,
                max_score=1.0,
                passed=False,
                feedback="Total weight is zero",
                details={"error": "zero_weight"}
            )
        
        weighted_score = 0.0
        weighted_max_score = 0.0
        all_feedback = []
        combined_details = {}
        
        for (result, weight) in results:
            weighted_score += (result.score / result.max_score) * weight
            weighted_max_score += weight
            all_feedback.append(f"[{weight}x] {result.feedback}")
            combined_details.update(result.details)
        
        final_score = weighted_score / total_weight
        
        return GradeResult(
            score=final_score,
            max_score=1.0,
            passed=final_score >= 0.7,  # Default threshold
            feedback=" | ".join(all_feedback),
            details=combined_details
        )
    
    def _all_pass(self, results: List[tuple]) -> GradeResult:
        """All graders must pass."""
        all_passed = all(result.passed for result, _ in results)
        feedback_parts = [result.feedback for result, _ in results]
        
        return GradeResult(
            score=1.0 if all_passed else 0.0,
            max_score=1.0,
            passed=all_passed,
            feedback=" AND ".join(feedback_parts),
            details={"strategy": "all_pass", "individual_results": len(results)}
        )
    
    def _any_pass(self, results: List[tuple]) -> GradeResult:
        """Any grader passing is sufficient."""
        any_passed = any(result.passed for result, _ in results)
        feedback_parts = [result.feedback for result, _ in results]
        
        return GradeResult(
            score=1.0 if any_passed else 0.0,
            max_score=1.0,
            passed=any_passed,
            feedback=" OR ".join(feedback_parts),
            details={"strategy": "any_pass", "individual_results": len(results)}
        )


class GraderFactory:
    """Factory for creating grader instances."""
    
    _graders = {}
    
    @classmethod
    def register_grader(cls, grader_type: GraderType, grader_class: type):
        """Register a grader class for a specific type."""
        cls._graders[grader_type] = grader_class
    
    @classmethod
    def create_grader(cls, config: GraderConfig) -> BaseGrader:
        """Create a grader instance for the given configuration."""
        if config.grader_type not in cls._graders:
            raise ValueError(f"No grader registered for type: {config.grader_type}")
        
        grader_class = cls._graders[config.grader_type]
        grader = grader_class(config)
        
        if not grader.validate_config():
            raise ValueError(f"Invalid configuration for grader: {config.name}")
        
        return grader
    
    @classmethod
    def list_grader_types(cls) -> List[GraderType]:
        """List all registered grader types."""
        return list(cls._graders.keys())
