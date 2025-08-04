#!/usr/bin/env python3
"""
Python 3.10+ Compatibility Test Script
Tests specific packages for Python 3.10+ compatibility
"""

import subprocess
import sys
import json
from pathlib import Path

def test_package_import(package_name: str) -> dict:
    """Test if a package can be imported successfully"""
    try:
        __import__(package_name)
        return {
            'package': package_name,
            'import_success': True,
            'error': None
        }
    except ImportError as e:
        return {
            'package': package_name,
            'import_success': False,
            'error': str(e)
        }
    except Exception as e:
        return {
            'package': package_name,
            'import_success': False,
            'error': f"Unexpected error: {str(e)}"
        }

def test_python310_features():
    """Test Python 3.10+ specific features"""
    features = {}
    
    # Test pattern matching (Python 3.10+)
    try:
        match_result = None
        match 1:
            case 1:
                match_result = "Pattern matching works"
        features['pattern_matching'] = True
    except SyntaxError:
        features['pattern_matching'] = False
    
    # Test union types (Python 3.10+)
    try:
        from typing import Union
        x: Union[int, str] = 1
        features['union_types'] = True
    except:
        features['union_types'] = False
    
    # Test parenthesized context managers (Python 3.10+)
    try:
        with (open('/dev/null', 'r') if sys.platform != 'win32' else open('nul', 'r')):
            pass
        features['parenthesized_context_managers'] = True
    except:
        features['parenthesized_context_managers'] = False
    
    return features

def check_python_version():
    """Check current Python version and capabilities"""
    version_info = {
        'version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        'version_tuple': sys.version_info,
        'is_310_plus': sys.version_info >= (3, 10),
        'is_311_plus': sys.version_info >= (3, 11),
        'is_312_plus': sys.version_info >= (3, 12),
    }
    return version_info

def main():
    print("🐍 Python 3.10+ Compatibility Test")
    print("=" * 40)
    
    # Check Python version
    version_info = check_python_version()
    print(f"Python version: {version_info['version']}")
    print(f"Python 3.10+: {'✅' if version_info['is_310_plus'] else '❌'}")
    print(f"Python 3.11+: {'✅' if version_info['is_311_plus'] else '❌'}")
    print(f"Python 3.12+: {'✅' if version_info['is_312_plus'] else '❌'}")
    print()
    
    # Test Python 3.10+ features
    if version_info['is_310_plus']:
        print("Testing Python 3.10+ features:")
        features = test_python310_features()
        for feature, supported in features.items():
            status = "✅" if supported else "❌"
            print(f"  {feature}: {status}")
        print()
    
    # Test key packages
    key_packages = [
        'fastapi',
        'pydantic', 
        'openai',
        'pandas',
        'numpy',
        'requests',
        'sqlalchemy',
        'alembic',
        'pytest',
        'uvicorn'
    ]
    
    print("Testing key package imports:")
    results = []
    
    for package in key_packages:
        result = test_package_import(package)
        results.append(result)
        status = "✅" if result['import_success'] else "❌"
        print(f"  {package}: {status}")
        if not result['import_success']:
            print(f"    Error: {result['error']}")
    
    print()
    
    # Summary
    successful_imports = sum(1 for r in results if r['import_success'])
    print(f"📊 Summary: {successful_imports}/{len(results)} packages imported successfully")
    
    if version_info['is_310_plus']:
        print("✅ You're running Python 3.10+ - great for modern development!")
    else:
        print("⚠️  Consider upgrading to Python 3.10+ for better features and performance")
    
    # Save results
    report = {
        'python_version': version_info,
        'python310_features': test_python310_features() if version_info['is_310_plus'] else None,
        'package_tests': results,
        'summary': {
            'total_packages': len(results),
            'successful_imports': successful_imports,
            'failed_imports': len(results) - successful_imports
        }
    }
    
    with open('python310_compatibility_test.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Test report saved to: python310_compatibility_test.json")

if __name__ == "__main__":
    main() 