"""Tool call accuracy grader for evaluating first-attempt tool calling correctness."""

from typing import Any, Dict, List, Optional
import json


class ToolCallAccuracyGrader:
    """Grade tool calls based on accuracy of first attempt."""
    
    def __init__(self):
        self.name = "tool_call_accuracy"
    
    def grade(self, run_result: Dict[str, Any], expected: Dict[str, Any]) -> Dict[str, Any]:
        """
        Grade tool calling accuracy.
        
        Args:
            run_result: The actual tool calls made by the model
            expected: Expected tool call and arguments
            
        Returns:
            Dict with score breakdown and total score
        """
        if not run_result.get("tool_calls"):
            return {
                "score": 0.0,
                "breakdown": {
                    "tool_name_correct": 0.0,
                    "args_present": 0.0, 
                    "args_correct": 0.0
                },
                "reasoning": "No tool calls made"
            }
            
        # Get first tool call
        first_call = run_result["tool_calls"][0]
        expected_tool = expected.get("expected_tool", "")
        expected_args = expected.get("expected_args", {})
        
        # Score components
        tool_name_score = 1.0 if first_call.get("name") == expected_tool else 0.0
        
        # Check if args are present
        actual_args = first_call.get("arguments", {})
        if isinstance(actual_args, str):
            try:
                actual_args = json.loads(actual_args)
            except json.JSONDecodeError:
                actual_args = {}
        
        args_present_score = 1.0 if actual_args else 0.0
        
        # Check argument correctness
        args_correct_score = 0.0
        if expected_args and actual_args:
            # Calculate overlap percentage
            matching_keys = 0
            matching_values = 0
            
            for key, expected_value in expected_args.items():
                if key in actual_args:
                    matching_keys += 1
                    # Handle workspace_root template replacement
                    actual_value = actual_args[key]
                    if "{{ workspace_root }}" in str(expected_value):
                        expected_value = str(expected_value).replace("{{ workspace_root }}", "")
                        if expected_value in str(actual_value):
                            matching_values += 1
                    elif actual_value == expected_value:
                        matching_values += 1
            
            if expected_args:
                args_correct_score = matching_values / len(expected_args)
        elif not expected_args and not actual_args:
            args_correct_score = 1.0
            
        # Weighted scoring: tool name (40%), args present (30%), args correct (30%)
        total_score = (tool_name_score * 0.4 + 
                      args_present_score * 0.3 + 
                      args_correct_score * 0.3)
        
        return {
            "score": total_score,
            "breakdown": {
                "tool_name_correct": tool_name_score,
                "args_present": args_present_score,
                "args_correct": args_correct_score
            },
            "reasoning": f"Tool: {first_call.get('name')} (expected: {expected_tool}), Args match: {args_correct_score:.1%}"
        }


def get_grader() -> ToolCallAccuracyGrader:
    """Factory function to get grader instance."""
    return ToolCallAccuracyGrader()
