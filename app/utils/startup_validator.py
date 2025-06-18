"""
Startup validation utilities for production deployment.
Validates environment configuration and system requirements.
"""
import os
import logging
from typing import List, Dict, Any
from pathlib import Path

from ..utils.config import get_config

logger = logging.getLogger(__name__)


class StartupValidationError(Exception):
    """Raised when startup validation fails."""
    pass


class StartupValidator:
    """Validates system configuration and requirements on startup."""
    
    def __init__(self):
        self.settings = get_config()
        self.validation_errors: List[str] = []
        self.validation_warnings: List[str] = []
    
    def validate_all(self) -> Dict[str, Any]:
        """
        Run all validation checks.
        
        Returns:
            Dict with validation results and status
            
        Raises:
            StartupValidationError: If critical validations fail
        """
        logger.info("Starting system validation...")
        
        # Reset validation state
        self.validation_errors.clear()
        self.validation_warnings.clear()
        
        # Run validation checks
        self._validate_environment_variables()
        self._validate_directories()
        self._validate_database()
        self._validate_api_keys()
        self._validate_client_configurations()
        
        # Prepare results
        results = {
            "status": "success" if not self.validation_errors else "failed",
            "errors": self.validation_errors,
            "warnings": self.validation_warnings,
            "checks_passed": 5 - len(self.validation_errors),
            "total_checks": 5
        }
        
        # Log results
        if self.validation_errors:
            logger.error(f"Startup validation failed with {len(self.validation_errors)} errors")
            for error in self.validation_errors:
                logger.error(f"  - {error}")
            raise StartupValidationError(f"System validation failed: {', '.join(self.validation_errors)}")
        
        if self.validation_warnings:
            logger.warning(f"Startup validation completed with {len(self.validation_warnings)} warnings")
            for warning in self.validation_warnings:
                logger.warning(f"  - {warning}")
        else:
            logger.info("All startup validations passed successfully")
        
        return results
    
    def _validate_environment_variables(self) -> None:
        """Validate required environment variables."""
        # Critical variables for production
        critical_vars = ["JWT_SECRET_KEY"]
        
        # Service-specific variables (optional for development/testing)
        service_vars = [
            "ANTHROPIC_API_KEY",
            "MAILGUN_API_KEY", 
            "MAILGUN_DOMAIN"
        ]
        
        # Check critical variables
        missing_critical = []
        for var in critical_vars:
            value = os.getenv(var)
            if not value:
                missing_critical.append(var)
        
        if missing_critical:
            self.validation_errors.append(f"Missing critical environment variables: {', '.join(missing_critical)}")
        
        # Check service variables (warnings only)
        missing_service = []
        for var in service_vars:
            value = os.getenv(var)
            if not value:
                missing_service.append(var)
            elif var.endswith("_KEY") and len(value) < 10:
                self.validation_warnings.append(f"{var} appears to be too short (< 10 chars)")
        
        if missing_service:
            self.validation_warnings.append(f"Missing service environment variables (will run in degraded mode): {', '.join(missing_service)}")
        
        # Optional variables with warnings
        optional_vars = {
            "MAILGUN_WEBHOOK_SIGNING_KEY": "Webhook signature verification disabled",
            "ANTHROPIC_MODEL": "Using default Claude model"
        }
        
        for var, warning in optional_vars.items():
            if not os.getenv(var):
                self.validation_warnings.append(f"{var} not set - {warning}")
    
    def _validate_directories(self) -> None:
        """Validate required directories exist."""
        required_dirs = [
            "data",
            "clients/active", 
            "logs"
        ]
        
        missing_dirs = []
        for dir_path in required_dirs:
            if not Path(dir_path).exists():
                missing_dirs.append(dir_path)
        
        if missing_dirs:
            self.validation_errors.append(f"Missing required directories: {', '.join(missing_dirs)}")
        
        # Check permissions
        for dir_path in ["data", "logs"]:
            if Path(dir_path).exists() and not os.access(dir_path, os.W_OK):
                self.validation_errors.append(f"No write permission for directory: {dir_path}")
    
    def _validate_database(self) -> None:
        """Validate database connection and schema."""
        try:
            from sqlalchemy import create_engine, text
            from ..database.connection import DATABASE_URL
            
            # Test database connection
            engine = create_engine(DATABASE_URL)
            with engine.connect() as conn:
                # Test basic query
                result = conn.execute(text("SELECT 1")).fetchone()
                if not result:
                    self.validation_errors.append("Database connection test failed")
                
                # Check required tables exist
                required_tables = ["users", "user_sessions", "clients", "alembic_version"]
                for table in required_tables:
                    try:
                        conn.execute(text(f"SELECT 1 FROM {table} LIMIT 1"))
                    except Exception:
                        self.validation_errors.append(f"Required table missing: {table}")
                
        except Exception as e:
            self.validation_errors.append(f"Database validation failed: {str(e)}")
    
    def _validate_api_keys(self) -> None:
        """Validate external API connectivity."""
        # Test Anthropic API (only if API key is provided)
        if self.settings.anthropic_api_key:
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=self.settings.anthropic_api_key)
                # Note: We don't actually call the API here to avoid costs
                # Just validate the client can be created
                if not client.api_key:
                    self.validation_errors.append("Anthropic API key validation failed")
            except ImportError:
                self.validation_warnings.append("Anthropic package not installed - AI features will be unavailable")
            except Exception as e:
                self.validation_errors.append(f"Anthropic API validation failed: {str(e)}")
        
        # Test Mailgun API key format
        mailgun_key = self.settings.mailgun_api_key  
        if mailgun_key and not mailgun_key.startswith("key-"):
            self.validation_warnings.append("Mailgun API key does not start with 'key-' - may be invalid format")
        
        # Validate domain format
        mailgun_domain = self.settings.mailgun_domain
        if mailgun_domain and not ("." in mailgun_domain and len(mailgun_domain) > 3):
            self.validation_errors.append("Mailgun domain appears invalid")
    
    def _validate_client_configurations(self) -> None:
        """Validate client configuration files."""
        clients_dir = Path("clients/active")
        if not clients_dir.exists():
            return  # Already handled in directory validation
        
        client_dirs = [d for d in clients_dir.iterdir() if d.is_dir()]
        if not client_dirs:
            self.validation_warnings.append("No client configurations found in clients/active/")
            return
        
        for client_dir in client_dirs:
            client_id = client_dir.name
            required_files = [
                "client-config.yaml",
                "routing-rules.yaml", 
                "categories.yaml"
            ]
            
            missing_files = []
            for file_name in required_files:
                if not (client_dir / file_name).exists():
                    missing_files.append(file_name)
            
            if missing_files:
                self.validation_warnings.append(
                    f"Client {client_id} missing config files: {', '.join(missing_files)}"
                )


def validate_startup() -> Dict[str, Any]:
    """
    Convenience function to run startup validation.
    
    Returns:
        Validation results dictionary
        
    Raises:
        StartupValidationError: If validation fails
    """
    validator = StartupValidator()
    return validator.validate_all()