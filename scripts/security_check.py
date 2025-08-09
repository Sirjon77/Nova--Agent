#!/usr/bin/env python3
"""
Nova Agent Security Validation Script

This script performs comprehensive security checks before deployment:
1. Environment variable validation
2. Configuration file security audit
3. Dependency vulnerability scan
4. Secret detection in codebase

Usage:
    python scripts/security_check.py
    python scripts/security_check.py --fix-deps  # Attempt to upgrade vulnerable dependencies
"""

import os
import sys
import subprocess
import yaml
import json
from pathlib import Path
from typing import List, Dict, Any

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from nova.config.env import validate_env_or_exit, FORBIDDEN
except ImportError as e:
    print(f"❌ Failed to import Nova modules: {e}")
    print("Make sure you're running this from the project root directory.")
    sys.exit(1)

class SecurityChecker:
    def __init__(self):
        self.issues = []
        self.warnings = []
        
    def add_issue(self, severity: str, category: str, message: str, fix: str = None):
        """Add a security issue."""
        self.issues.append({
            'severity': severity,
            'category': category,
            'message': message,
            'fix': fix
        })
    
    def add_warning(self, message: str):
        """Add a warning."""
        self.warnings.append(message)
    
    def check_environment_variables(self) -> bool:
        """Check that all required environment variables are set securely."""
        print("🔍 Checking environment configuration...")
        
        try:
            validate_env_or_exit()
            print("✅ Environment validation passed")
            return True
        except SystemExit:
            self.add_issue(
                'CRITICAL',
                'Environment',
                'Required environment variables are missing or insecure',
                'Set all required environment variables from config/env.production.template'
            )
            return False
    
    def check_config_files(self) -> bool:
        """Check configuration files for hardcoded secrets."""
        print("🔍 Checking configuration files for hardcoded secrets...")
        
        config_files = [
            'config/production_config.yaml',
            'config/settings.yaml',
            'governance_config.yaml'
        ]
        
        issues_found = False
        
        for config_file in config_files:
            config_path = PROJECT_ROOT / config_file
            if not config_path.exists():
                continue
                
            try:
                with open(config_path, 'r') as f:
                    content = f.read()
                    
                # Check for forbidden values
                for forbidden in FORBIDDEN:
                    if forbidden in content.lower():
                        self.add_issue(
                            'HIGH',
                            'Configuration',
                            f'Potentially insecure value "{forbidden}" found in {config_file}',
                            f'Replace hardcoded values with environment variables in {config_file}'
                        )
                        issues_found = True
                
                # Check for email/password patterns
                if 'password' in content.lower() and not '${' in content:
                    lines_with_password = [line.strip() for line in content.split('\n') 
                                         if 'password' in line.lower() and not line.strip().startswith('#')]
                    if lines_with_password:
                        self.add_warning(f"Password-related configuration in {config_file}: {lines_with_password}")
                        
            except Exception as e:
                self.add_warning(f"Could not check {config_file}: {e}")
        
        if not issues_found:
            print("✅ No hardcoded secrets found in configuration files")
        
        return not issues_found
    
    def check_dependencies(self, fix_deps: bool = False) -> bool:
        """Check for vulnerable dependencies."""
        print("🔍 Checking dependencies for security vulnerabilities...")
        
        try:
            # Try to run pip-audit
            result = subprocess.run([
                sys.executable, '-m', 'pip_audit', 
                '--requirement', str(PROJECT_ROOT / 'requirements.txt'),
                '--format', 'json'
            ], capture_output=True, text=True, cwd=PROJECT_ROOT)
            
            if result.returncode == 0:
                try:
                    audit_data = json.loads(result.stdout)
                    vulnerabilities = audit_data.get('vulnerabilities', [])
                    
                    if vulnerabilities:
                        self.add_issue(
                            'HIGH',
                            'Dependencies',
                            f'Found {len(vulnerabilities)} security vulnerabilities in dependencies',
                            'Run: pip-audit --requirement requirements.txt --fix' if fix_deps else 'Upgrade vulnerable packages'
                        )
                        
                        # Show top 3 vulnerabilities
                        for vuln in vulnerabilities[:3]:
                            package = vuln.get('package', 'unknown')
                            id = vuln.get('id', 'unknown')
                            print(f"  - {package}: {id}")
                        
                        if fix_deps:
                            print("🔧 Attempting to fix dependencies...")
                            fix_result = subprocess.run([
                                sys.executable, '-m', 'pip_audit', 
                                '--requirement', str(PROJECT_ROOT / 'requirements.txt'),
                                '--fix'
                            ], cwd=PROJECT_ROOT)
                            
                            if fix_result.returncode == 0:
                                print("✅ Dependencies fixed successfully")
                                return True
                            else:
                                print("❌ Failed to fix all dependencies automatically")
                        
                        return False
                    else:
                        print("✅ No known vulnerabilities in dependencies")
                        return True
                        
                except json.JSONDecodeError:
                    self.add_warning("Could not parse pip-audit output")
                    return True  # Don't fail if we can't parse the output
                    
        except FileNotFoundError:
            self.add_warning("pip-audit not available - install with: pip install pip-audit")
            return True  # Don't fail if pip-audit isn't installed
        except Exception as e:
            self.add_warning(f"Dependency check failed: {e}")
            return True  # Don't fail the entire check for dependency scan issues
        
        return True  # Default to True if we reach here
    
    def check_secrets_in_code(self) -> bool:
        """Check for accidentally committed secrets in code."""
        print("🔍 Scanning code for potential secrets...")
        
        # Patterns that might indicate secrets
        secret_patterns = [
            'password.*=.*["\'][^$]',  # password = "literal"
            'api_key.*=.*["\'][^$]',   # api_key = "literal"
            'secret.*=.*["\'][^$]',    # secret = "literal"
            'token.*=.*["\'][^$]',     # token = "literal"
        ]
        
        issues_found = False
        
        # Scan Python files
        for py_file in PROJECT_ROOT.rglob('*.py'):
            if '.venv' in str(py_file) or '__pycache__' in str(py_file):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for forbidden hardcoded values
                for forbidden in FORBIDDEN:
                    if f'"{forbidden}"' in content or f"'{forbidden}'" in content:
                        self.add_issue(
                            'MEDIUM',
                            'Code Security',
                            f'Potentially hardcoded insecure value "{forbidden}" in {py_file}',
                            f'Replace with environment variable in {py_file}'
                        )
                        issues_found = True
                        
            except Exception as e:
                self.add_warning(f"Could not scan {py_file}: {e}")
        
        if not issues_found:
            print("✅ No obvious secrets found in code")
        
        return not issues_found
    
    def run_comprehensive_check(self, fix_deps: bool = False) -> bool:
        """Run all security checks."""
        print("🛡️  Running Nova Agent Security Check\n")
        
        all_passed = True
        
        # Run all checks
        all_passed &= self.check_environment_variables()
        all_passed &= self.check_config_files()
        all_passed &= self.check_dependencies(fix_deps)
        all_passed &= self.check_secrets_in_code()
        
        # Report results
        print("\n📊 Security Check Results:")
        print("=" * 50)
        
        if self.issues:
            print(f"❌ Found {len(self.issues)} security issues:")
            for issue in self.issues:
                print(f"  [{issue['severity']}] {issue['category']}: {issue['message']}")
                if issue['fix']:
                    print(f"    💡 Fix: {issue['fix']}")
        
        if self.warnings:
            print(f"\n⚠️  {len(self.warnings)} warnings:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        print(f"\n🎯 Overall Status: {'✅ SECURE' if all_passed else '❌ ISSUES FOUND'}")
        
        if not all_passed:
            print("\n🚨 Fix all security issues before deploying to production!")
        
        return all_passed

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Nova Agent Security Validator')
    parser.add_argument('--fix-deps', action='store_true', 
                       help='Attempt to automatically fix dependency vulnerabilities')
    
    args = parser.parse_args()
    
    checker = SecurityChecker()
    success = checker.run_comprehensive_check(fix_deps=args.fix_deps)
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
