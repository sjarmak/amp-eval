"""Secure secret management for amp-eval."""

import os
import json
import logging
from typing import Optional
from functools import lru_cache

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False

try:
    import hvac
    VAULT_AVAILABLE = True
except ImportError:
    VAULT_AVAILABLE = False

logger = logging.getLogger(__name__)


class SecretError(Exception):
    """Base exception for secret management errors."""
    pass


class SecretManager:
    """Secure secret manager supporting multiple backends."""
    
    def __init__(self):
        self.aws_client = None
        self.vault_client = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize available secret management clients."""
        # AWS Secrets Manager
        if AWS_AVAILABLE:
            try:
                self.aws_client = boto3.client('secretsmanager')
                logger.info("AWS Secrets Manager client initialized")
            except NoCredentialsError:
                logger.warning("AWS credentials not found, skipping AWS Secrets Manager")
        
        # HashiCorp Vault
        if VAULT_AVAILABLE:
            vault_url = os.getenv('VAULT_ADDR')
            vault_token = os.getenv('VAULT_TOKEN')
            if vault_url and vault_token:
                try:
                    self.vault_client = hvac.Client(url=vault_url, token=vault_token)
                    if self.vault_client.is_authenticated():
                        logger.info("Vault client initialized and authenticated")
                    else:
                        logger.warning("Vault authentication failed")
                        self.vault_client = None
                except Exception as e:
                    logger.warning(f"Failed to initialize Vault client: {e}")
    
    @lru_cache(maxsize=32)
    def get_secret(self, secret_name: str, backend: Optional[str] = None) -> str:
        """
        Retrieve secret from configured backend.
        
        Args:
            secret_name: Name/path of the secret
            backend: Force specific backend ('aws', 'vault', 'env')
        
        Returns:
            Secret value as string
            
        Raises:
            SecretError: If secret cannot be retrieved
        """
        backends_to_try = []
        
        if backend:
            backends_to_try = [backend]
        else:
            # Try in order of preference
            if self.aws_client:
                backends_to_try.append('aws')
            if self.vault_client:
                backends_to_try.append('vault')
            backends_to_try.append('env')
        
        last_error = None
        for backend_name in backends_to_try:
            try:
                if backend_name == 'aws':
                    return self._get_aws_secret(secret_name)
                elif backend_name == 'vault':
                    return self._get_vault_secret(secret_name)
                elif backend_name == 'env':
                    return self._get_env_secret(secret_name)
            except Exception as e:
                last_error = e
                logger.debug(f"Failed to get secret from {backend_name}: {e}")
                continue
        
        raise SecretError(f"Failed to retrieve secret '{secret_name}' from any backend. Last error: {last_error}")
    
    def _get_aws_secret(self, secret_name: str) -> str:
        """Retrieve secret from AWS Secrets Manager."""
        if not self.aws_client:
            raise SecretError("AWS Secrets Manager not available")
        
        try:
            response = self.aws_client.get_secret_value(SecretId=secret_name)
            secret_data = response['SecretString']
            
            # Handle JSON secrets
            try:
                parsed = json.loads(secret_data)
                if isinstance(parsed, dict) and 'api_key' in parsed:
                    return parsed['api_key']
                elif isinstance(parsed, dict) and len(parsed) == 1:
                    return next(iter(parsed.values()))
            except json.JSONDecodeError:
                pass
            
            return secret_data
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceNotFoundException':
                raise SecretError(f"Secret '{secret_name}' not found in AWS Secrets Manager")
            elif error_code == 'AccessDeniedException':
                raise SecretError(f"Access denied to secret '{secret_name}' in AWS Secrets Manager")
            else:
                raise SecretError(f"AWS Secrets Manager error: {e}")
    
    def _get_vault_secret(self, secret_path: str) -> str:
        """Retrieve secret from HashiCorp Vault."""
        if not self.vault_client:
            raise SecretError("Vault client not available")
        
        try:
            # Support both KV v1 and v2 engines
            if '/data/' in secret_path:
                # KV v2 path (includes /data/)
                response = self.vault_client.secrets.kv.v2.read_secret_version(
                    path=secret_path.split('/data/')[-1],
                    mount_point=secret_path.split('/')[0]
                )
                secret_data = response['data']['data']
            else:
                # KV v1 path or generic
                response = self.vault_client.read(secret_path)
                secret_data = response['data']
            
            # Return specific key or first value
            if 'api_key' in secret_data:
                return secret_data['api_key']
            elif 'value' in secret_data:
                return secret_data['value']
            elif len(secret_data) == 1:
                return next(iter(secret_data.values()))
            else:
                raise SecretError(f"Ambiguous secret data in Vault at '{secret_path}'")
                
        except Exception as e:
            raise SecretError(f"Vault error: {e}")
    
    def _get_env_secret(self, env_var: str) -> str:
        """Retrieve secret from environment variable."""
        value = os.getenv(env_var)
        if value is None:
            raise SecretError(f"Environment variable '{env_var}' not set")
        return value


# Global instance
_secret_manager = SecretManager()

# Legacy API key functions removed - this tool evaluates Amp only
# If you need to access external APIs directly, use appropriate SDK clients
