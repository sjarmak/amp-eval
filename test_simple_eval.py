#!/usr/bin/env python3
"""
Simple test to isolate the hanging issue
"""
import sys
import os
import time

# Add src to path for imports
sys.path.insert(0, '/workspaces/amp-eval/src')

from amp_eval.amp_runner import AmpRunner

def test_single_evaluation():
    """Test a single evaluation to see where it hangs"""
    print("=== Simple Evaluation Test ===")
    
    try:
        print("1. Creating AmpRunner...")
        runner = AmpRunner("config/agent_settings.yaml")
        print("   ✅ AmpRunner created successfully")
        
        print("2. Testing model selection...")
        model = runner.select_model("test prompt")
        print(f"   ✅ Selected model: {model}")
        
        print("3. Testing run_amp method...")
        print("   (This is where it might hang)")
        
        start_time = time.time()
        result = runner.run_amp("test", "sonnet-4", ".")
        elapsed = time.time() - start_time
        
        print(f"   ✅ Completed in {elapsed:.2f}s")
        print(f"   Success: {result['success']}")
        print(f"   Return code: {result['returncode']}")
        
        if result['stderr']:
            print(f"   Stderr: {result['stderr'][:200]}")
        
        return result
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_single_evaluation()
