#!/usr/bin/env python3
"""
Run baseline evaluation to generate initial performance metrics.
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add adapters to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'adapters'))

from amp_runner import AmpRunner


def run_baseline_evaluation():
    """Run basic evaluation tests to establish baseline performance."""
    runner = AmpRunner()
    
    # Test cases covering core model selection scenarios
    test_cases = [
        {
            "name": "oracle_trigger_test",
            "prompt": "consult the oracle: how should I optimize this database query?",
            "expected_model": "o3",
            "description": "Oracle trigger should select o3 model"
        },
        {
            "name": "cli_flag_test", 
            "prompt": "debug this authentication issue",
            "cli_args": ["--try-gpt5"],
            "expected_model": "gpt-5",
            "description": "CLI flag should override to gpt-5"
        },
        {
            "name": "large_diff_rule_test",
            "prompt": "refactor this large codebase",
            "diff_lines": 50,
            "expected_model": "gpt-5",
            "description": "Large diff should trigger gpt-5 upgrade"
        },
        {
            "name": "multi_file_rule_test",
            "prompt": "update multiple components",
            "touched_files": 3,
            "expected_model": "gpt-5", 
            "description": "Multi-file changes should trigger gpt-5 upgrade"
        },
        {
            "name": "default_fallback_test",
            "prompt": "simple code fix",
            "expected_model": "sonnet-4",
            "description": "Simple tasks should use default model"
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"Running: {test_case['name']}")
        
        # Extract test parameters
        prompt = test_case["prompt"]
        cli_args = test_case.get("cli_args", [])
        diff_lines = test_case.get("diff_lines", 0)
        touched_files = test_case.get("touched_files", 0)
        expected_model = test_case["expected_model"]
        
        # Test model selection
        selected_model = runner.select_model(
            prompt, cli_args, diff_lines, touched_files
        )
        
        # Record results
        result = {
            "test_name": test_case["name"],
            "description": test_case["description"],
            "prompt": prompt,
            "expected_model": expected_model,
            "selected_model": selected_model,
            "success": selected_model == expected_model,
            "timestamp": datetime.now().isoformat()
        }
        
        results.append(result)
        
        # Print status
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"  {status} - Expected: {expected_model}, Got: {selected_model}")
    
    # Calculate summary statistics
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r["success"])
    success_rate = (passed_tests / total_tests) * 100
    
    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "failed_tests": total_tests - passed_tests,
        "success_rate_percent": success_rate,
        "test_results": results
    }
    
    # Save results
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / f"baseline_evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Print summary
    print("\n" + "="*50)
    print("BASELINE EVALUATION SUMMARY")
    print("="*50)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {success_rate:.1f}%")
    print(f"Results saved to: {output_file}")
    
    if success_rate == 100.0:
        print("🎉 All tests passed! Model selection logic is working correctly.")
    else:
        print("⚠️  Some tests failed. Review the results for debugging.")
    
    return summary


if __name__ == "__main__":
    run_baseline_evaluation()
