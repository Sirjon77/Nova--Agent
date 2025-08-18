"""
Enhanced Security Validation for Nova Agent

This module provides comprehensive security validation for environment variables,
ensuring they meet security requirements and best practices.
"""

import os
import re
import secrets
from typing import List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class SecurityValidationResult:
    """Result of security validation check."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]


class SecurityValidator:
    """Enhanced security validator for environment variables."""
    
    def __init__(self):
        self.validation_rules = {
            "OPENAI_API_KEY": {
                "required": True,
                "pattern": r"^sk-[a-zA-Z0-9]{32,}$",
                "description": "OpenAI API key starting with 'sk-'",
                "min_length": 35
            },
            "JWT_SECRET_KEY": {
                "required": True,
                "pattern": r"^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]{32,}$",
                "description": "Strong JWT secret (32+ chars, no spaces)",
                "min_length": 32,
                "forbidden_values": ["change-me", "default", "secret", "key"]
            },
            "WEAVIATE_API_KEY": {
                "required": True,
                "pattern": r"^[a-zA-Z0-9\-_]{20,}$",
                "description": "Weaviate API key (20+ chars)",
                "min_length": 20
            },
            "EMAIL_PASSWORD": {
                "required": True,
                "pattern": r"^[a-zA-Z0-9!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]{16,}$",
                "description": "Email app password (16+ chars)",
                "min_length": 16,
                "forbidden_values": ["your_app_password_here", "password", "123456"]
            }
        }
    
    def validate_environment(self) -> SecurityValidationResult:
        """Validate all environment variables for security compliance."""
        errors = []
        warnings = []
        
        for var_name, rules in self.validation_rules.items():
            value = os.getenv(var_name)
            
            # Check if required
            if rules.get("required", False) and not value:
                errors.append(f"Missing required environment variable: {var_name}")
                continue
            
            if not value:
                continue  # Skip validation for optional variables
            
            # Check minimum length
            if "min_length" in rules and len(value) < rules["min_length"]:
                errors.append(f"{var_name}: Value too short (min {rules['min_length']} chars)")
            
            # Check pattern
            if "pattern" in rules and not re.match(rules["pattern"], value):
                errors.append(f"{var_name}: Invalid format - {rules['description']}")
            
            # Check forbidden values
            if "forbidden_values" in rules and value in rules["forbidden_values"]:
                errors.append(f"{var_name}: Using forbidden value '{value}'")
            
            # Security warnings
            if self._is_weak_secret(value):
                warnings.append(f"{var_name}: Consider using a stronger secret")
        
        # Additional security checks
        self._check_common_vulnerabilities(errors, warnings)
        
        return SecurityValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _is_weak_secret(self, value: str) -> bool:
        """Check if a secret is potentially weak."""
        if len(value) < 16:
            return True
        
        # Check for common weak patterns
        weak_patterns = [
            r"^[a-z]+$",  # All lowercase
            r"^[A-Z]+$",  # All uppercase
            r"^[0-9]+$",  # All numbers
            r"^(.)\1+$",  # Repeated characters
        ]
        
        for pattern in weak_patterns:
            if re.match(pattern, value):
                return True
        
        return False
    
    def _check_common_vulnerabilities(self, errors: List[str], warnings: List[str]):
        """Check for common security vulnerabilities."""
        # Check for development secrets in production
        if os.getenv("NODE_ENV") == "production" or os.getenv("ENVIRONMENT") == "production":
            dev_secrets = ["test", "dev", "development", "localhost"]
            for var_name, value in os.environ.items():
                if any(secret in value.lower() for secret in dev_secrets):
                    warnings.append(f"{var_name}: Contains development-like value in production")
        
        # Check for exposed secrets in logs
        if os.getenv("LOG_LEVEL", "").upper() == "DEBUG":
            warnings.append("DEBUG logging enabled - ensure secrets are not logged")
    
    def generate_secure_secret(self, length: int = 64) -> str:
        """Generate a cryptographically secure secret."""
        return secrets.token_urlsafe(length)
    
    def validate_jwt_secret_strength(self, secret: str) -> Tuple[bool, List[str]]:
        """Validate JWT secret strength specifically."""
        issues = []
        
        if len(secret) < 32:
            issues.append("JWT secret should be at least 32 characters long")
        
        if not re.search(r"[A-Z]", secret):
            issues.append("JWT secret should contain uppercase letters")
        
        if not re.search(r"[a-z]", secret):
            issues.append("JWT secret should contain lowercase letters")
        
        if not re.search(r"[0-9]", secret):
            issues.append("JWT secret should contain numbers")
        
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", secret):
            issues.append("JWT secret should contain special characters")
        
        return len(issues) == 0, issues


def get_required_env(var_name: str, validator: Optional[SecurityValidator] = None) -> str:
    """Fetch an environment variable with enhanced validation."""
    val = os.getenv(var_name)
    if not val:
        raise RuntimeError(f"Missing required environment variable: {var_name}")
    
    if validator:
        result = validator.validate_environment()
        if not result.is_valid:
            raise RuntimeError(f"Security validation failed for {var_name}: {'; '.join(result.errors)}")
    
    return val


def launch_setup() -> None:
    """Enhanced launch setup with security validation."""
    validator = SecurityValidator()
    
    # Validate all environment variables
    result = validator.validate_environment()
    
    if not result.is_valid:
        print("❌ Security validation failed:")
        for error in result.errors:
            print(f"   - {error}")
        raise RuntimeError("Environment validation failed")
    
    if result.warnings:
        print("⚠️  Security warnings:")
        for warning in result.warnings:
            print(f"   - {warning}")
    
    # Verify critical secrets
    required_vars = [
        "OPENAI_API_KEY",
        "WEAVIATE_URL", 
        "WEAVIATE_API_KEY",
        "JWT_SECRET_KEY"
    ]
    
    for var in required_vars:
        get_required_env(var, validator)
    
    print("✅ All required secrets validated. Launching Nova Agent...") 