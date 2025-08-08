#!/usr/bin/env python3
"""
Check amp CLI authentication status
"""
import subprocess
import os
import time

def check_amp_auth():
    """Check if amp CLI is properly authenticated"""
    print("=== Amp Authentication Check ===")
    
    # Check environment variables
    print("Environment variables:")
    print(f"  AMP_API_KEY: {'SET' if os.environ.get('AMP_API_KEY') else 'NOT SET'}")
    print(f"  AMP_URL: {os.environ.get('AMP_URL', 'default')}")
    print(f"  HOME: {os.environ.get('HOME', 'NOT SET')}")
    
    # Check if amp config exists
    home = os.environ.get('HOME', '/home/vscode')
    config_path = os.path.join(home, '.config', 'amp', 'settings.json')
    print(f"\nConfig file check:")
    print(f"  Path: {config_path}")
    print(f"  Exists: {os.path.exists(config_path)}")
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                content = f.read()
                print(f"  Content length: {len(content)} chars")
        except Exception as e:
            print(f"  Error reading: {e}")
    
    # Test basic amp commands
    print("\nTesting amp commands:")
    
    # Test 1: Version (should always work)
    try:
        result = subprocess.run(
            ["amp", "--version"], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        print(f"  amp --version: SUCCESS (exit {result.returncode})")
        print(f"    Output: {result.stdout.strip()}")
    except Exception as e:
        print(f"  amp --version: FAILED - {e}")
    
    # Test 2: List threads (requires auth)
    try:
        result = subprocess.run(
            ["amp", "threads", "list"], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        print(f"  amp threads list: {'SUCCESS' if result.returncode == 0 else 'FAILED'} (exit {result.returncode})")
        if result.stderr:
            print(f"    Error: {result.stderr.strip()[:100]}")
    except Exception as e:
        print(f"  amp threads list: FAILED - {e}")
    
    # Test 3: Simple execute command
    try:
        print("\n  Testing execute command (may hang)...")
        start = time.time()
        result = subprocess.run(
            ["amp", "--dangerously-allow-all", "-x", "echo test"], 
            capture_output=True, 
            text=True, 
            timeout=15
        )
        elapsed = time.time() - start
        print(f"  amp execute: {'SUCCESS' if result.returncode == 0 else 'FAILED'} in {elapsed:.1f}s (exit {result.returncode})")
        if result.stdout:
            print(f"    Output: {result.stdout.strip()[:100]}")
        if result.stderr:
            print(f"    Error: {result.stderr.strip()[:100]}")
    except subprocess.TimeoutExpired:
        print("  amp execute: TIMEOUT after 15s")
    except Exception as e:
        print(f"  amp execute: FAILED - {e}")

if __name__ == "__main__":
    check_amp_auth()
