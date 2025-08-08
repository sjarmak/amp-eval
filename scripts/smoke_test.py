#!/usr/bin/env python3
"""
Smoke test for Amp Evaluation Suite.
Tests basic functionality: tool calling, model selection, and cost tracking.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    try:
        from adapters.amp_runner import AmpRunner
        
        # Initialize runner
        runner = AmpRunner()
        
        # Run a simple test
        result = runner.run_amp('List files', 'sonnet-4')
        
        # Check tool calling
        if result.get('tool_calls'):
            print('✅ Tool calling test passed')
        else:
            print('❌ Tool calling failed')
            
        # Check model selection
        if result.get('model') == 'sonnet-4':
            print('✅ Model selection working')
        else:
            print('❌ Model selection failed')
            
        # Check cost tracking
        if result.get('token_usage'):
            print('✅ Cost tracking active')
        else:
            print('❌ Cost tracking failed')
            
        return True
        
    except Exception as e:
        print(f'❌ Smoke test failed: {e}')
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
