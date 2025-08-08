#!/usr/bin/env python3
"""
Built-in grader implementations.
"""

import re
import subprocess
from typing import Dict, Any, Callable
from .base import BaseGrader, GraderConfig, GradeResult, GraderType, GraderFactory


class ExactMatchGrader(BaseGrader):
    """Grader that checks for exact string match."""
    
    def grade(self, response: str, expected: Any = None, context: Dict[str, Any] = None) -> GradeResult:
        if expected is None:
            return GradeResult(
                score=0.0,
                max_score=1.0,
                passed=False,
                feedback="No expected value provided",
                details={"error": "missing_expected"}
            )
        
        case_sensitive = self.config.parameters.get("case_sensitive", True)
        
        if not case_sensitive:
            response = response.lower()
            expected = str(expected).lower()
        
        matches = response.strip() == str(expected).strip()
        
        return GradeResult(
            score=1.0 if matches else 0.0,
            max_score=1.0,
            passed=matches,
            feedback=f"Expected: '{expected}', Got: '{response}'" if not matches else "Exact match",
            details={"case_sensitive": case_sensitive}
        )
    
    def get_grader_info(self) -> Dict[str, Any]:
        return {
            "type": "exact_match",
            "description": "Checks for exact string match",
            "parameters": ["case_sensitive"]
        }


class ContainsGrader(BaseGrader):
    """Grader that checks if response contains expected text."""
    
    def grade(self, response: str, expected: Any = None, context: Dict[str, Any] = None) -> GradeResult:
        if expected is None:
            return GradeResult(
                score=0.0,
                max_score=1.0,
                passed=False,
                feedback="No expected value provided",
                details={"error": "missing_expected"}
            )
        
        case_sensitive = self.config.parameters.get("case_sensitive", True)
        
        search_text = response
        target_text = str(expected)
        
        if not case_sensitive:
            search_text = search_text.lower()
            target_text = target_text.lower()
        
        contains = target_text in search_text
        
        return GradeResult(
            score=1.0 if contains else 0.0,
            max_score=1.0,
            passed=contains,
            feedback=f"Looking for: '{expected}'" + (" - Found" if contains else " - Not found"),
            details={"case_sensitive": case_sensitive}
        )
    
    def get_grader_info(self) -> Dict[str, Any]:
        return {
            "type": "contains",
            "description": "Checks if response contains expected text",
            "parameters": ["case_sensitive"]
        }


class RegexGrader(BaseGrader):
    """Grader that uses regular expression matching."""
    
    def grade(self, response: str, expected: Any = None, context: Dict[str, Any] = None) -> GradeResult:
        pattern = expected or self.config.parameters.get("pattern")
        if not pattern:
            return GradeResult(
                score=0.0,
                max_score=1.0,
                passed=False,
                feedback="No regex pattern provided",
                details={"error": "missing_pattern"}
            )
        
        flags = 0
        if not self.config.parameters.get("case_sensitive", True):
            flags |= re.IGNORECASE
        
        try:
            matches = re.search(pattern, response, flags) is not None
            
            return GradeResult(
                score=1.0 if matches else 0.0,
                max_score=1.0,
                passed=matches,
                feedback=f"Pattern: '{pattern}'" + (" - Matched" if matches else " - No match"),
                details={"pattern": pattern, "flags": flags}
            )
        except re.error as e:
            return GradeResult(
                score=0.0,
                max_score=1.0,
                passed=False,
                feedback=f"Invalid regex pattern: {e}",
                details={"error": "invalid_regex", "pattern": pattern}
            )
    
    def get_grader_info(self) -> Dict[str, Any]:
        return {
            "type": "regex",
            "description": "Uses regular expression matching",
            "parameters": ["pattern", "case_sensitive"]
        }


class FunctionGrader(BaseGrader):
    """Grader that uses a custom function for evaluation."""
    
    def grade(self, response: str, expected: Any = None, context: Dict[str, Any] = None) -> GradeResult:
        function_name = self.config.parameters.get("function")
        if not function_name:
            return GradeResult(
                score=0.0,
                max_score=1.0,
                passed=False,
                feedback="No grading function specified",
                details={"error": "missing_function"}
            )
        
        try:
            # For security, only allow pre-defined functions
            grading_function = self._get_grading_function(function_name)
            if not grading_function:
                return GradeResult(
                    score=0.0,
                    max_score=1.0,
                    passed=False,
                    feedback=f"Unknown grading function: {function_name}",
                    details={"error": "unknown_function"}
                )
            
            # Call the grading function
            result = grading_function(response, expected, context or {})
            
            # Ensure result is a GradeResult
            if not isinstance(result, GradeResult):
                # Try to convert from simple return values
                if isinstance(result, bool):
                    result = GradeResult(
                        score=1.0 if result else 0.0,
                        max_score=1.0,
                        passed=result,
                        feedback=f"Function {function_name} returned: {result}"
                    )
                elif isinstance(result, (int, float)):
                    result = GradeResult(
                        score=float(result),
                        max_score=1.0,
                        passed=result >= self.config.pass_threshold,
                        feedback=f"Function {function_name} score: {result}"
                    )
                else:
                    return GradeResult(
                        score=0.0,
                        max_score=1.0,
                        passed=False,
                        feedback=f"Function {function_name} returned invalid type: {type(result)}",
                        details={"error": "invalid_return_type"}
                    )
            
            return result
            
        except Exception as e:
            return GradeResult(
                score=0.0,
                max_score=1.0,
                passed=False,
                feedback=f"Function {function_name} failed: {str(e)}",
                details={"error": "function_exception", "exception": str(e)}
            )
    
    def _get_grading_function(self, function_name: str) -> Callable:
        """Get a pre-defined grading function by name."""
        # Built-in grading functions
        functions = {
            "test_passes": self._test_passes_function,
            "code_compiles": self._code_compiles_function,
            "length_check": self._length_check_function,
        }
        return functions.get(function_name)
    
    def _test_passes_function(self, response: str, expected: Any, context: Dict[str, Any]) -> GradeResult:
        """Run tests and check if they pass."""
        test_command = context.get("test_command", "pytest")
        working_dir = context.get("working_dir", ".")
        
        try:
            result = subprocess.run(
                test_command.split(),
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            passed = result.returncode == 0
            return GradeResult(
                score=1.0 if passed else 0.0,
                max_score=1.0,
                passed=passed,
                feedback=f"Tests {'passed' if passed else 'failed'}",
                details={
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            )
        except subprocess.TimeoutExpired:
            return GradeResult(
                score=0.0,
                max_score=1.0,
                passed=False,
                feedback="Tests timed out",
                details={"error": "timeout"}
            )
        except Exception as e:
            return GradeResult(
                score=0.0,
                max_score=1.0,
                passed=False,
                feedback=f"Test execution failed: {str(e)}",
                details={"error": "execution_failed", "exception": str(e)}
            )
    
    def _code_compiles_function(self, response: str, expected: Any, context: Dict[str, Any]) -> GradeResult:
        """Check if code compiles without errors."""
        language = context.get("language", "python")
        
        if language == "python":
            try:
                compile(response, "<string>", "exec")
                return GradeResult(
                    score=1.0,
                    max_score=1.0,
                    passed=True,
                    feedback="Code compiles successfully",
                    details={"language": language}
                )
            except SyntaxError as e:
                return GradeResult(
                    score=0.0,
                    max_score=1.0,
                    passed=False,
                    feedback=f"Syntax error: {str(e)}",
                    details={"error": "syntax_error", "language": language}
                )
        else:
            return GradeResult(
                score=0.0,
                max_score=1.0,
                passed=False,
                feedback=f"Unsupported language: {language}",
                details={"error": "unsupported_language"}
            )
    
    def _length_check_function(self, response: str, expected: Any, context: Dict[str, Any]) -> GradeResult:
        """Check if response meets length requirements."""
        min_length = context.get("min_length", 0)
        max_length = context.get("max_length", float('inf'))
        
        length = len(response)
        within_bounds = min_length <= length <= max_length
        
        return GradeResult(
            score=1.0 if within_bounds else 0.0,
            max_score=1.0,
            passed=within_bounds,
            feedback=f"Length {length} (required: {min_length}-{max_length})",
            details={"length": length, "min_length": min_length, "max_length": max_length}
        )
    
    def get_grader_info(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "description": "Uses custom function for evaluation",
            "parameters": ["function"],
            "built_in_functions": ["test_passes", "code_compiles", "length_check"]
        }


# Register built-in graders
GraderFactory.register_grader(GraderType.EXACT_MATCH, ExactMatchGrader)
GraderFactory.register_grader(GraderType.CONTAINS, ContainsGrader)
GraderFactory.register_grader(GraderType.REGEX, RegexGrader)
GraderFactory.register_grader(GraderType.FUNCTION, FunctionGrader)
