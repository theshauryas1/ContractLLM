import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class SecretsManager:
    """
    Enterprise Secrets Manager supporting multiple cloud secret management providers:
    - Environment Variables (fallback / local dev)
    - AWS Secrets Manager
    - Azure Key Vault
    - Google Secret Manager
    """

    def __init__(self, provider: Optional[str] = None) -> None:
        # Load provider configuration from the environment
        self.provider = provider or os.getenv("SECRETS_PROVIDER", "env").lower()
        logger.info(f"Initializing SecretsManager with provider: {self.provider}")

    def get_secret(self, secret_name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Retrieve a secret value from the active provider.
        """
        # 1. Fallback / Explicit Env Provider
        if self.provider == "env":
            return os.getenv(secret_name, default)

        # 2. Azure Key Vault
        if self.provider == "azure":
            return self._get_azure_secret(secret_name, default)

        # 3. AWS Secrets Manager
        if self.provider == "aws":
            return self._get_aws_secret(secret_name, default)

        # 4. Google Secret Manager
        if self.provider == "google":
            return self._get_google_secret(secret_name, default)

        logger.warning(f"Unknown secrets provider '{self.provider}'. Falling back to environment variables.")
        return os.getenv(secret_name, default)

    def _get_azure_secret(self, secret_name: str, default: Optional[str]) -> Optional[str]:
        """Retrieves secret from Azure Key Vault."""
        vault_url = os.getenv("AZURE_KEYVAULT_URL")
        if not vault_url:
            logger.error("Azure secrets provider chosen, but AZURE_KEYVAULT_URL environment variable is missing.")
            return os.getenv(secret_name, default)

        try:
            from azure.identity import DefaultAzureCredential
            from azure.keyvault.secrets import SecretClient
            
            # Format secret name to comply with Azure naming limits (alphanumeric and dashes only)
            formatted_name = secret_name.replace("_", "-")
            
            credential = DefaultAzureCredential()
            client = SecretClient(vault_url=vault_url, credential=credential)
            
            retrieved = client.get_secret(formatted_name)
            return retrieved.value
        except ImportError:
            logger.error("azure-identity or azure-keyvault-secrets SDK not installed. Falling back to environment variables.")
            return os.getenv(secret_name, default)
        except Exception as e:
            logger.error(f"Error fetching secret '{secret_name}' from Azure Key Vault: {e}")
            return os.getenv(secret_name, default)

    def _get_aws_secret(self, secret_name: str, default: Optional[str]) -> Optional[str]:
        """Retrieves secret from AWS Secrets Manager."""
        region = os.getenv("AWS_REGION_NAME", "us-east-1")
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            session = boto3.session.Session()
            client = session.client(service_name="secretsmanager", region_name=region)
            
            response = client.get_secret_value(SecretId=secret_name)
            if "SecretString" in response:
                return response["SecretString"]
            return response.get("SecretBinary")
        except ImportError:
            logger.error("boto3 SDK not installed. Falling back to environment variables.")
            return os.getenv(secret_name, default)
        except Exception as e:
            logger.error(f"Error fetching secret '{secret_name}' from AWS Secrets Manager: {e}")
            return os.getenv(secret_name, default)

    def _get_google_secret(self, secret_name: str, default: Optional[str]) -> Optional[str]:
        """Retrieves secret from Google Secret Manager."""
        project_id = os.getenv("GCP_PROJECT_ID")
        if not project_id:
            logger.error("Google Secret Manager chosen, but GCP_PROJECT_ID environment variable is missing.")
            return os.getenv(secret_name, default)

        try:
            from google.cloud import secretmanager
            
            client = secretmanager.SecretManagerServiceClient()
            # Construct standard Google Secret Manager path
            name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
            
            response = client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except ImportError:
            logger.error("google-cloud-secret-manager SDK not installed. Falling back to environment variables.")
            return os.getenv(secret_name, default)
        except Exception as e:
            logger.error(f"Error fetching secret '{secret_name}' from Google Secret Manager: {e}")
            return os.getenv(secret_name, default)

# Singleton global manager instance
_manager = None

def get_secret(secret_name: str, default: Optional[str] = None) -> Optional[str]:
    """Helper method to access the global SecretsManager instance."""
    global _manager
    if _manager is None:
        _manager = SecretsManager()
    return _manager.get_secret(secret_name, default)
