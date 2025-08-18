from __future__ import annotations

import os
import sys
from typing import Optional
from pydantic import BaseModel, Field


FORBIDDEN = {"change-me", "default", "secret", "key", "password"}


class JWTSettings(BaseModel):
    algorithm: str = Field(default=os.getenv("JWT_ALG", "HS256"))
    secret_key: Optional[str] = Field(default=os.getenv("JWT_SECRET_KEY"))
    token_version: int = Field(default=int(os.getenv("JWT_TOKEN_VERSION", "1")))

    def validate_keys(self) -> None:
        if self.algorithm == "HS256":
            if not self.secret_key:
                raise ValueError("JWT_SECRET_KEY must be set when JWT_ALG=HS256")
            if self.secret_key in FORBIDDEN or len(self.secret_key) < 32:
                raise ValueError("JWT_SECRET_KEY too weak; set a strong 32+ char secret")
        elif self.algorithm == "RS256":
            # Not currently supported by the app
            raise ValueError("RS256 not supported in this build; set JWT_ALG=HS256")
        else:
            raise ValueError(f"Unsupported JWT_ALG: {self.algorithm}")


class AppEnv(BaseModel):
    """Nova application environment variables. These must be set in production."""
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    
    # Admin credentials must be provided via environment (no insecure defaults)
    admin_username: str = Field(default=os.getenv("NOVA_ADMIN_USERNAME", "admin"))
    admin_password: Optional[str] = Field(default=os.getenv("NOVA_ADMIN_PASSWORD"))
    
    # Required API keys and service URLs
    openai_api_key: Optional[str] = Field(default=os.getenv("OPENAI_API_KEY"))
    redis_url: Optional[str] = Field(default=os.getenv("REDIS_URL"))
    weaviate_url: Optional[str] = Field(default=os.getenv("WEAVIATE_URL"))
    
    # Optional integrations
    slack_webhook_url: Optional[str] = Field(default=os.getenv("SLACK_WEBHOOK_URL"))
    
    # Email configuration (for alerts)
    email_sender: Optional[str] = Field(default=os.getenv("EMAIL_SENDER"))
    email_password: Optional[str] = Field(default=os.getenv("EMAIL_PASSWORD"))
    email_receiver: Optional[str] = Field(default=os.getenv("EMAIL_RECEIVER"))


def validate_env_or_exit() -> None:
    """
    Validate required environment variables. Exit with a clear error if any are missing
    or if the JWT keys are invalid. This function should run before app startup.
    """
    try:
        env = AppEnv()
        missing_vars = []
        insecure_vars = []
        
        # Check for missing critical environment variables
        if not env.admin_password:
            missing_vars.append("NOVA_ADMIN_PASSWORD")
        elif env.admin_password in FORBIDDEN:
            insecure_vars.append("NOVA_ADMIN_PASSWORD")
            
        if not env.openai_api_key:
            missing_vars.append("OPENAI_API_KEY")
        elif env.openai_api_key in FORBIDDEN:
            insecure_vars.append("OPENAI_API_KEY")
            
        if not env.redis_url:
            missing_vars.append("REDIS_URL")
            
        if not env.weaviate_url:
            missing_vars.append("WEAVIATE_URL")
        
        # Check email configuration for secure values
        if env.email_password and env.email_password in FORBIDDEN:
            insecure_vars.append("EMAIL_PASSWORD")
        
        # Build error message
        errors = []
        if missing_vars:
            errors.append(f"Missing required environment variables: {', '.join(missing_vars)}")
        if insecure_vars:
            errors.append(f"Insecure values found in: {', '.join(insecure_vars)}")
        
        # Validate JWT settings
        env.jwt.validate_keys()
        
        # If we have any errors, show them and exit
        if errors:
            print("[ENV VALIDATION] Critical configuration errors:", file=sys.stderr)
            for error in errors:
                print(f"  - {error}", file=sys.stderr)
            print("\nSet proper environment variables before starting the application.", file=sys.stderr)
            sys.exit(1)
            
    except Exception as e:
        print(f"[ENV VALIDATION] {e}", file=sys.stderr)
        sys.exit(1)


