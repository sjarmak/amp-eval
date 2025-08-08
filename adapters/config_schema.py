"""
Pydantic schemas for configuration validation.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, field_validator


class OracleTriggerConfig(BaseModel):
    """Oracle trigger configuration."""
    phrase: str
    model: str
    description: Optional[str] = None


class CLIFlagConfig(BaseModel):
    """CLI flag configuration."""
    flag: str
    model: str
    description: Optional[str] = None


class EnvVarConfig(BaseModel):
    """Environment variable configuration."""
    name: str
    valid_values: List[str]
    description: Optional[str] = None


class RuleConfig(BaseModel):
    """Rule configuration."""
    name: str
    condition: str
    target_model: str
    description: Optional[str] = None


class TokenBudgetConfig(BaseModel):
    """Token budget thresholds."""
    sonnet_4: int = 8000
    gpt_5: int = 16000
    o3: int = 32000
    description: Optional[str] = None


class AgentSettingsConfig(BaseModel):
    """Complete agent settings configuration schema."""
    default_model: str
    oracle_trigger: OracleTriggerConfig
    cli_flag_gpt5: CLIFlagConfig
    env_var: EnvVarConfig
    rules: List[RuleConfig] = []
    token_budget_threshold: Optional[TokenBudgetConfig] = None
    selection_precedence: Optional[Dict[int, str]] = None

    @field_validator('default_model')
    @classmethod
    def validate_default_model(cls, v):
        """Validate default model is a recognized value."""
        valid_models = ['sonnet-4', 'gpt-5', 'o3']
        if v not in valid_models:
            raise ValueError(f'default_model must be one of {valid_models}')
        return v

    @field_validator('rules')
    @classmethod
    def validate_rules_target_models(cls, v):
        """Validate all rules target valid models."""
        valid_models = ['sonnet-4', 'gpt-5', 'o3']
        for rule in v:
            if rule.target_model not in valid_models:
                raise ValueError(f'Rule "{rule.name}" target_model must be one of {valid_models}')
        return v

    @field_validator('oracle_trigger')
    @classmethod
    def validate_oracle_model(cls, v):
        """Validate oracle trigger model."""
        if v.model not in ['o3']:
            raise ValueError('Oracle trigger model should typically be "o3"')
        return v
