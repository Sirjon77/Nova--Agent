"""
Secret Management and Rotation for Nova Agent

This module provides advanced secret management capabilities including
automatic rotation, secure storage, and audit logging.
"""

import os
import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class SecretMetadata:
    """Metadata for a secret including rotation and audit info."""
    name: str
    created_at: datetime
    last_rotated: datetime
    expires_at: Optional[datetime]
    hash: str
    source: str  # 'env', 'vault', 'file'
    rotation_policy: str  # 'manual', 'auto', 'never'


class SecretManager:
    """Advanced secret management with rotation and audit capabilities."""
    
    def __init__(self, audit_log_path: str = "logs/secret_audit.json"):
        self.audit_log_path = Path(audit_log_path)
        self.audit_log_path.parent.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        # Rotation policies (in days)
        self.rotation_policies = {
            "JWT_SECRET_KEY": 90,  # Rotate JWT secrets every 90 days
            "OPENAI_API_KEY": 365,  # API keys typically last longer
            "WEAVIATE_API_KEY": 180,
            "EMAIL_PASSWORD": 90,
        }
        
        # Load existing audit log
        self.audit_log = self._load_audit_log()
    
    def get_secret(self, name: str, required: bool = True) -> Optional[str]:
        """Get a secret with rotation checking and audit logging."""
        value = os.getenv(name)
        
        if not value and required:
            raise RuntimeError(f"Missing required secret: {name}")
        
        if value:
            self._audit_secret_access(name, value)
            self._check_rotation_needed(name, value)
        
        return value
    
    def _audit_secret_access(self, name: str, value: str):
        """Audit secret access for security monitoring."""
        access_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "secret_name": name,
            "action": "access",
            "hash": self._hash_secret(value),
            "source": "environment"
        }
        
        self.audit_log.append(access_record)
        self._save_audit_log()
        
        self.logger.info(f"Secret accessed: {name}")
    
    def _check_rotation_needed(self, name: str, value: str):
        """Check if a secret needs rotation based on policy."""
        if name not in self.rotation_policies:
            return
        
        # Get last rotation info
        last_rotation = self._get_last_rotation(name)
        if not last_rotation:
            self._record_rotation(name, value)
            return
        
        days_since_rotation = (datetime.utcnow() - last_rotation).days
        max_age = self.rotation_policies[name]
        
        if days_since_rotation > max_age:
            self.logger.warning(
                f"Secret {name} is {days_since_rotation} days old "
                f"(max: {max_age} days). Consider rotation."
            )
    
    def _get_last_rotation(self, name: str) -> Optional[datetime]:
        """Get the last rotation time for a secret."""
        for record in reversed(self.audit_log):
            if (record.get("secret_name") == name and 
                record.get("action") == "rotation"):
                return datetime.fromisoformat(record["timestamp"])
        return None
    
    def _record_rotation(self, name: str, value: str):
        """Record a secret rotation."""
        rotation_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "secret_name": name,
            "action": "rotation",
            "hash": self._hash_secret(value),
            "source": "environment"
        }
        
        self.audit_log.append(rotation_record)
        self._save_audit_log()
        
        self.logger.info(f"Secret rotation recorded: {name}")
    
    def _hash_secret(self, value: str) -> str:
        """Create a hash of a secret for audit purposes."""
        return hashlib.sha256(value.encode()).hexdigest()[:16]
    
    def _load_audit_log(self) -> List[Dict[str, Any]]:
        """Load the audit log from file."""
        if not self.audit_log_path.exists():
            return []
        
        try:
            with open(self.audit_log_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load audit log: {e}")
            return []
    
    def _save_audit_log(self):
        """Save the audit log to file."""
        try:
            with open(self.audit_log_path, 'w') as f:
                json.dump(self.audit_log, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save audit log: {e}")
    
    def get_secret_health_report(self) -> Dict[str, Any]:
        """Generate a health report for all secrets."""
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "secrets": {},
            "warnings": [],
            "critical_issues": []
        }
        
        for name, max_age in self.rotation_policies.items():
            value = os.getenv(name)
            if not value:
                report["critical_issues"].append(f"Missing required secret: {name}")
                continue
            
            last_rotation = self._get_last_rotation(name)
            if not last_rotation:
                report["secrets"][name] = {
                    "status": "unknown_age",
                    "last_rotation": None,
                    "days_since_rotation": None
                }
                continue
            
            days_since_rotation = (datetime.utcnow() - last_rotation).days
            status = "healthy"
            
            if days_since_rotation > max_age:
                status = "needs_rotation"
                report["warnings"].append(
                    f"Secret {name} is {days_since_rotation} days old "
                    f"(max: {max_age} days)"
                )
            elif days_since_rotation > max_age * 0.8:
                status = "approaching_rotation"
                report["warnings"].append(
                    f"Secret {name} will need rotation in "
                    f"{max_age - days_since_rotation} days"
                )
            
            report["secrets"][name] = {
                "status": status,
                "last_rotation": last_rotation.isoformat(),
                "days_since_rotation": days_since_rotation,
                "max_age_days": max_age
            }
        
        return report
    
    def validate_all_secrets(self) -> bool:
        """Validate all secrets are present and healthy."""
        health_report = self.get_secret_health_report()
        
        if health_report["critical_issues"]:
            for issue in health_report["critical_issues"]:
                self.logger.error(issue)
            return False
        
        if health_report["warnings"]:
            for warning in health_report["warnings"]:
                self.logger.warning(warning)
        
        return True


# Global secret manager instance
secret_manager = SecretManager()


def get_secure_secret(name: str, required: bool = True) -> Optional[str]:
    """Get a secret with enhanced security and audit logging."""
    return secret_manager.get_secret(name, required)


def validate_secrets() -> bool:
    """Validate all secrets are present and healthy."""
    return secret_manager.validate_all_secrets()


def get_secret_health() -> Dict[str, Any]:
    """Get a health report for all secrets."""
    return secret_manager.get_secret_health_report() 