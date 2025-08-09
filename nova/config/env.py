from __future__ import annotations

import os
import sys
from pydantic import BaseModel, Field


FORBIDDEN = {"change-me", "default", "secret", "key", "password"}


class JWTSettings(BaseModel):
    algorithm: str = Field(default=os.getenv("JWT_ALG", "HS256"))
    secret_key: str | None = Field(default=os.getenv("JWT_SECRET_KEY"))
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
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    slack_webhook_url: str | None = Field(default=os.getenv("SLACK_WEBHOOK_URL"))


def validate_env_or_exit() -> None:
    try:
        env = AppEnv()
        env.jwt.validate_keys()
    except Exception as e:
        print(f"[ENV VALIDATION] {e}", file=sys.stderr)
        sys.exit(1)


