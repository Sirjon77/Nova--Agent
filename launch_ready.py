
"""
Enhanced Launch Setup for Nova Agent with Security Validation

This module provides secure startup validation and configuration checking
for the Nova Agent system.
"""

import os
import sys
from typing import Dict, Any, List


def startup_message():
    """Return startup message for Nova Agent."""
    return "Nova Agent Launch Ready - Security Validated."


def get_required_env(var_name: str) -> str:
    """Fetch an environment variable or raise a runtime error if missing."""
    val = os.getenv(var_name)
    if not val:
        raise RuntimeError(f"Missing required environment variable: {var_name}")
    return val


def launch_setup() -> Dict[str, Any]:
    """Enhanced setup function with security validation for Nova Agent launch."""
    print("🔐 Starting Nova Agent Security Validation...")
    
    # Import security validator
    try:
        from security_validator import SecurityValidator, launch_setup as security_launch
        validator = SecurityValidator()
        
        # Run comprehensive security validation
        security_launch()
        
        print("✅ Security validation completed successfully")
        
    except ImportError:
        print("⚠️  Security validator not available, using basic validation")
        # Fallback to basic validation
        _basic_security_validation()
    
    # Verify critical secrets are present
    required_vars = [
        "OPENAI_API_KEY",
        "WEAVIATE_URL", 
        "WEAVIATE_API_KEY",
        "JWT_SECRET_KEY"
    ]
    
    validated_vars = {}
    for var in required_vars:
        try:
            validated_vars[var] = get_required_env(var)
            print(f"✅ {var}: Validated")
        except RuntimeError as e:
            print(f"❌ {e}")
            raise
    
    # Check optional integrations
    optional_vars = [
        "EMAIL_SENDER", "EMAIL_PASSWORD", "EMAIL_RECEIVER",
        "NOTION_TOKEN", "METRICOOL_API_KEY", "CONVERTKIT_API_KEY",
        "GUMROAD_API_KEY"
    ]
    
    configured_integrations = []
    for var in optional_vars:
        if os.getenv(var):
            configured_integrations.append(var)
            print(f"✅ {var}: Configured")
        else:
            print(f"ℹ️  {var}: Not configured (optional)")
    
    print(f"🚀 Nova Agent ready to launch with {len(configured_integrations)} integrations")
    
    return {
        "status": "ready",
        "version": "2.5",
        "components": ["core", "nlp", "memory", "governance", "analytics"],
        "security": "validated",
        "integrations": configured_integrations,
        "validated_vars": list(validated_vars.keys())
    }


def _basic_security_validation():
    """Basic security validation when enhanced validator is not available."""
    print("🔍 Running basic security validation...")
    
    # Check for forbidden values
    forbidden_values = ["change-me", "your_app_password_here", "API_KEY", "notion-token"]
    
    for var_name, value in os.environ.items():
        if value in forbidden_values:
            raise RuntimeError(f"Security violation: {var_name} contains forbidden value '{value}'")
    
    # Check for weak JWT secrets
    jwt_secret = os.getenv("JWT_SECRET_KEY")
    if jwt_secret and len(jwt_secret) < 32:
        raise RuntimeError("JWT_SECRET_KEY is too weak (minimum 32 characters required)")
    
    print("✅ Basic security validation passed")
