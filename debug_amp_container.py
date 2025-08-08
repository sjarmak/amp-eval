#!/usr/bin/env python3
"""
Debug script to test amp CLI in container environment
"""
import subprocess
import time
import sys
import os

def test_amp_command(cmd, timeout=30):
    """Test an amp command with timeout and detailed output"""
    print(f"Testing command: {' '.join(cmd)}")
    start = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd="/workspaces/amp-eval"
        )
        
        elapsed = time.time() - start
        print(f"✅ Completed in {elapsed:.2f}s")
        print(f"Return code: {result.returncode}")
        
        if result.stdout:
            print("STDOUT:", result.stdout[:500])
        if result.stderr:
            print("STDERR:", result.stderr[:500])
        
        return result
        
    except subprocess.TimeoutExpired as e:
        print(f"❌ TIMEOUT after {timeout}s")
        return None
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return None

def main():
    print("=== Amp CLI Debug Test ===")
    print(f"Working directory: {os.getcwd()}")
    print(f"PATH: {os.environ.get('PATH', 'Not set')}")
    print(f"AMP_API_KEY set: {'Yes' if os.environ.get('AMP_API_KEY') else 'No'}")
    print(f"HOME: {os.environ.get('HOME', 'Not set')}")
    
    # Test 1: Check if amp is available
    print("\n1. Testing amp availability...")
    test_amp_command(["which", "amp"], 10)
    
    # Test 2: Check amp version/help
    print("\n2. Testing amp help...")
    test_amp_command(["amp", "--version"], 10)
    
    # Test 3: Check if amp is authenticated
    print("\n3. Testing amp authentication status...")
    test_amp_command(["amp", "threads", "list"], 10)
    
    # Test 4: Test basic amp command that should work
    print("\n4. Testing basic amp command...")
    test_amp_command(["amp", "--dangerously-allow-all", "-x", "echo hello"], 30)
    
    # Test 5: Test the exact command used in evaluation
    print("\n5. Testing evaluation command...")
    test_amp_command([
        "amp", "--dangerously-allow-all", "-x", 
        "List all Python files in the current directory"
    ], 60)
    
    # Test 6: Check if there are any blocking interactive prompts
    print("\n6. Testing with shorter timeout to see immediate failure...")
    test_amp_command([
        "amp", "--dangerously-allow-all", "-x", "test"
    ], 5)

if __name__ == "__main__":
    main()
