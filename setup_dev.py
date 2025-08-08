#!/usr/bin/env python3
"""
Development environment setup script for amp-eval.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> None:
    """Run a command and handle errors."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stderr:
            print(f"   Error: {e.stderr.strip()}")
        sys.exit(1)


def main():
    """Set up development environment."""
    print("🚀 Setting up amp-eval development environment")
    
    # Install package in development mode
    run_command([sys.executable, "-m", "pip", "install", "-e", ".[dev]"], 
                "Installing package in development mode")
    
    # Install pre-commit hooks
    run_command(["pre-commit", "install"], "Installing pre-commit hooks")
    
    # Run initial code formatting
    run_command(["black", "src/", "tests/"], "Formatting code with black")
    
    # Run linting
    run_command(["ruff", "check", "src/", "tests/", "--fix"], "Running ruff linter")
    
    # Run type checking
    try:
        run_command(["mypy", "src/amp_eval/"], "Running type checking")
    except SystemExit:
        print("⚠️  Type checking failed - this is expected for initial setup")
    
    # Verify CLI installation
    run_command(["amp-eval", "--version"], "Verifying CLI installation")
    
    print("\n🎉 Development environment setup complete!")
    print("\nNext steps:")
    print("  1. Run tests: pytest")
    print("  2. Try the CLI: amp-eval --help")
    print("  3. Validate config: amp-eval validate-config")


if __name__ == "__main__":
    main()
