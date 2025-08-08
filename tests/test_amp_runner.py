#!/usr/bin/env python3
"""
Unit tests for AmpRunner class - model selection logic and core functionality.
"""

import os
import pytest
import tempfile
import yaml
from unittest.mock import patch, MagicMock
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from adapters.amp_runner import AmpRunner


class TestAmpRunner:
    """Test suite for AmpRunner model selection and execution logic."""
    
    @pytest.fixture
    def temp_config(self):
        """Create temporary configuration for testing."""
        config_data = {
            'default_model': 'sonnet-4',
            'oracle_trigger': {'phrase': 'consult the oracle:', 'model': 'o3'},
            'cli_flag_gpt5': {'flag': '--try-gpt5', 'model': 'gpt-5'},
            'env_var': {'name': 'AMP_MODEL', 'valid_values': ['sonnet-4', 'gpt-5', 'o3']},
            'rules': [
                {'name': 'large_diff_upgrade', 'condition': 'diff_lines > 40', 'target_model': 'gpt-5'},
                {'name': 'multi_file_upgrade', 'condition': 'touched_files > 2', 'target_model': 'gpt-5'}
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = f.name
            
        yield config_path
        os.unlink(config_path)
    
    @pytest.fixture
    def runner(self, temp_config):
        """Create AmpRunner instance with test configuration."""
        return AmpRunner(config_path=temp_config)
    
    def test_select_model_oracle_trigger(self, runner):
        """Test oracle trigger has highest priority."""
        prompt = "consult the oracle: how should I implement this feature?"
        model = runner.select_model(prompt)
        assert model == 'o3'
    
    def test_select_model_oracle_case_insensitive(self, runner):
        """Test oracle trigger works case-insensitively."""
        prompt = "CONSULT THE ORACLE: help me debug this code"
        model = runner.select_model(prompt)
        assert model == 'o3'
    
    def test_select_model_cli_flag_override(self, runner):
        """Test CLI flag override works."""
        prompt = "fix this bug"
        cli_args = ['--try-gpt5']
        model = runner.select_model(prompt, cli_args)
        assert model == 'gpt-5'
    
    def test_select_model_env_var_override(self, runner):
        """Test environment variable override."""
        prompt = "refactor this code"
        with patch.dict(os.environ, {'AMP_MODEL': 'gpt-5'}):
            model = runner.select_model(prompt)
            assert model == 'gpt-5'
    
    def test_select_model_invalid_env_var(self, runner):
        """Test invalid environment variable falls through to rules."""
        prompt = "simple task"
        with patch.dict(os.environ, {'AMP_MODEL': 'invalid-model'}):
            model = runner.select_model(prompt)
            assert model == 'sonnet-4'  # Falls back to default
    
    def test_select_model_large_diff_rule(self, runner):
        """Test automatic upgrade for large diffs."""
        prompt = "refactor this large codebase"
        model = runner.select_model(prompt, diff_lines=50)
        assert model == 'gpt-5'
    
    def test_select_model_multi_file_rule(self, runner):
        """Test automatic upgrade for multi-file changes."""
        prompt = "update multiple components"
        model = runner.select_model(prompt, touched_files=3)
        assert model == 'gpt-5'
    
    def test_select_model_default_fallback(self, runner):
        """Test default model fallback."""
        prompt = "simple task"
        model = runner.select_model(prompt)
        assert model == 'sonnet-4'
    
    def test_precedence_oracle_beats_cli(self, runner):
        """Test oracle trigger overrides CLI flag."""
        prompt = "consult the oracle: analyze this code"
        cli_args = ['--try-gpt5']
        model = runner.select_model(prompt, cli_args)
        assert model == 'o3'  # Oracle should win
    
    def test_precedence_cli_beats_env(self, runner):
        """Test CLI flag overrides environment variable."""
        prompt = "debug this issue"
        cli_args = ['--try-gpt5']
        with patch.dict(os.environ, {'AMP_MODEL': 'sonnet-4'}):
            model = runner.select_model(prompt, cli_args)
            assert model == 'gpt-5'
    
    def test_evaluate_rule_large_diff(self, runner):
        """Test rule evaluation for large diffs."""
        rule = {'condition': 'diff_lines > 40', 'target_model': 'gpt-5'}
        assert runner._evaluate_rule(rule, diff_lines=50, touched_files=1) is True
        assert runner._evaluate_rule(rule, diff_lines=30, touched_files=1) is False
    
    def test_evaluate_rule_multi_file(self, runner):
        """Test rule evaluation for multiple files."""
        rule = {'condition': 'touched_files > 2', 'target_model': 'gpt-5'}
        assert runner._evaluate_rule(rule, diff_lines=10, touched_files=3) is True
        assert runner._evaluate_rule(rule, diff_lines=10, touched_files=2) is False
    
    def test_token_estimation(self, runner):
        """Test basic token estimation logic."""
        prompt = "test prompt"
        response = "test response"
        tokens = runner._estimate_tokens(prompt, response)
        expected = (len(prompt) + len(response)) // 4
        assert tokens == expected
    
    def test_config_loading_fallback(self):
        """Test configuration loading with missing file."""
        runner = AmpRunner(config_path="nonexistent.yaml")
        assert runner.config['default_model'] == 'sonnet-4'
        assert 'oracle_trigger' in runner.config
    
    @patch('subprocess.run')
    def test_run_amp_success(self, mock_subprocess, runner):
        """Test successful Amp execution."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Success: Task completed"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result
        
        result = runner.run_amp("test prompt", "sonnet-4", ".")
        
        assert result['success'] is True
        assert result['model'] == 'sonnet-4'
        assert result['stdout'] == "Success: Task completed"
        assert 'latency_s' in result
        assert 'tokens' in result
    
    @patch('subprocess.run')
    def test_run_amp_failure(self, mock_subprocess, runner):
        """Test failed Amp execution."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Error: Command failed"
        mock_subprocess.return_value = mock_result
        
        result = runner.run_amp("test prompt", "sonnet-4", ".")
        
        assert result['success'] is False
        assert result['stderr'] == "Error: Command failed"
    
    @patch('subprocess.run')
    def test_run_amp_timeout(self, mock_subprocess, runner):
        """Test Amp execution timeout."""
        from subprocess import TimeoutExpired
        mock_subprocess.side_effect = TimeoutExpired("amp", 300)
        
        result = runner.run_amp("test prompt", "sonnet-4", ".")
        
        assert result['success'] is False
        assert result['latency_s'] == 300.0
        assert "timed out" in result['stderr'].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
