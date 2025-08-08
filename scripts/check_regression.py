#!/usr/bin/env python3
"""
Check for performance regressions by comparing current results to baseline.
"""

import json
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

def load_results(file_path: str) -> Optional[Dict[str, Any]]:
    """Load results from JSON file, return None if file doesn't exist."""
    path = Path(file_path)
    if not path.exists():
        return None
    
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def calculate_accuracy(results: Dict[str, Any]) -> float:
    """Calculate accuracy percentage from results."""
    total = results.get('total_tasks', 0)
    successful = results.get('successful_tasks', 0)
    return (successful / total * 100) if total > 0 else 0

def check_regression(current_file: str, baseline_file: str, threshold: float = 0.05) -> bool:
    """
    Check if current results show regression compared to baseline.
    
    Args:
        current_file: Path to current results JSON
        baseline_file: Path to baseline results JSON  
        threshold: Regression threshold (e.g., 0.05 = 5% drop)
        
    Returns:
        True if regression detected, False otherwise
    """
    current = load_results(current_file)
    baseline = load_results(baseline_file)
    
    if not current:
        print(f"❌ Could not load current results from {current_file}")
        return True  # Treat as regression if we can't load results
        
    if not baseline:
        print(f"⚠️  No baseline found at {baseline_file}, skipping regression check")
        return False
        
    current_accuracy = calculate_accuracy(current)
    baseline_accuracy = calculate_accuracy(baseline)
    
    accuracy_drop = baseline_accuracy - current_accuracy
    regression_detected = accuracy_drop > (threshold * 100)
    
    print(f"Accuracy: {current_accuracy:.1f}% (baseline: {baseline_accuracy:.1f}%)")
    print(f"Change: {-accuracy_drop:+.1f}%")
    
    if regression_detected:
        print(f"🚨 REGRESSION DETECTED: Accuracy dropped by {accuracy_drop:.1f}% (threshold: {threshold*100:.1f}%)")
        return True
    else:
        print(f"✅ No regression detected (within {threshold*100:.1f}% threshold)")
        return False

def main():
    parser = argparse.ArgumentParser(description="Check for performance regressions")
    parser.add_argument("--current", required=True, help="Current results JSON file")
    parser.add_argument("--baseline", required=True, help="Baseline results JSON file")
    parser.add_argument("--threshold", type=float, default=0.05, 
                       help="Regression threshold (default: 0.05 = 5%)")
    
    args = parser.parse_args()
    
    regression_detected = check_regression(args.current, args.baseline, args.threshold)
    
    # Exit with non-zero code if regression detected
    sys.exit(1 if regression_detected else 0)

if __name__ == '__main__':
    main()
