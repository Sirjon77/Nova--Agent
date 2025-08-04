#!/usr/bin/env python3
"""
Python 3.10+ Dependency Support Checker v2
Improved version with better PyPI API handling
"""

import subprocess
import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional

def get_python_version() -> str:
    """Get current Python version"""
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

def parse_requirements(file_path: str) -> List[str]:
    """Parse requirements.txt and return package names"""
    packages = []
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                # Extract package name (remove version constraints and extras)
                package = re.split(r'[<>=!~\[\]]', line)[0].strip()
                if package:
                    packages.append(package)
    return list(set(packages))  # Remove duplicates

def check_package_python_support(package: str) -> Dict:
    """Check if a package supports Python 3.10+ using PyPI API"""
    import urllib.request
    import urllib.parse
    
    try:
        # Query PyPI API
        url = f"https://pypi.org/pypi/{package}/json"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read())
            
        # Get latest version info
        latest_version = data['info']['version']
        
        # Check Python version classifiers from info
        python_support = []
        if 'classifiers' in data['info']:
            for classifier in data['info']['classifiers']:
                if classifier.startswith('Programming Language :: Python ::'):
                    version_match = re.search(r'Programming Language :: Python :: (\d+\.\d+)', classifier)
                    if version_match:
                        python_support.append(version_match.group(1))
        
        # If no classifiers in info, check releases
        if not python_support and 'releases' in data:
            version_data = data['releases'].get(latest_version, [])
            for release in version_data:
                if 'classifiers' in release:
                    for classifier in release['classifiers']:
                        if classifier.startswith('Programming Language :: Python ::'):
                            version_match = re.search(r'Programming Language :: Python :: (\d+\.\d+)', classifier)
                            if version_match:
                                python_support.append(version_match.group(1))
        
        # Remove duplicates and sort
        python_support = sorted(list(set(python_support)), key=lambda x: float(x))
        
        # Check if Python 3.10+ is supported
        supports_310_plus = any(
            float(version) >= 3.10 for version in python_support
        )
        
        return {
            'package': package,
            'latest_version': latest_version,
            'python_support': python_support,
            'supports_310_plus': supports_310_plus,
            'status': 'SUPPORTED' if supports_310_plus else 'NOT_SUPPORTED'
        }
        
    except Exception as e:
        return {
            'package': package,
            'error': str(e),
            'status': 'ERROR'
        }

def check_with_pip_show(package: str) -> Dict:
    """Alternative method using pip show"""
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'show', package],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode == 0:
            # Parse pip show output
            lines = result.stdout.strip().split('\n')
            version = None
            requires = []
            
            for line in lines:
                if line.startswith('Version:'):
                    version = line.split(':', 1)[1].strip()
                elif line.startswith('Requires:'):
                    requires_str = line.split(':', 1)[1].strip()
                    if requires_str and requires_str != 'None':
                        requires = [r.strip() for r in requires_str.split(',')]
            
            return {
                'package': package,
                'installed_version': version,
                'requires': requires,
                'status': 'INSTALLED'
            }
        else:
            return {
                'package': package,
                'status': 'NOT_INSTALLED'
            }
            
    except Exception as e:
        return {
            'package': package,
            'error': str(e),
            'status': 'ERROR'
        }

def check_python_version_requirements() -> Dict:
    """Check Python version requirements for the project"""
    requirements = {
        'python_version': get_python_version(),
        'python_version_tuple': sys.version_info,
        'is_310_plus': sys.version_info >= (3, 10),
        'pip_version': None,
        'pip_check_result': None
    }
    
    # Get pip version
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            version_match = re.search(r'pip (\d+\.\d+\.\d+)', result.stdout)
            if version_match:
                requirements['pip_version'] = version_match.group(1)
    except Exception:
        pass
    
    # Run pip check
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'check'], 
                              capture_output=True, text=True)
        requirements['pip_check_result'] = {
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
    except Exception as e:
        requirements['pip_check_result'] = {'error': str(e)}
    
    return requirements

def main():
    print("🐍 Python 3.10+ Dependency Support Checker v2")
    print("=" * 55)
    
    # Check Python environment
    python_info = check_python_version_requirements()
    current_version = python_info['python_version']
    
    print(f"Current Python version: {current_version}")
    print(f"Pip version: {python_info['pip_version'] or 'Unknown'}")
    
    if python_info['is_310_plus']:
        print("✅ Running Python 3.10+")
    else:
        print("⚠️  Warning: You're not running Python 3.10+")
        print("   This check will verify if dependencies support Python 3.10+")
    
    # Check pip dependencies
    if python_info['pip_check_result']:
        if python_info['pip_check_result']['returncode'] == 0:
            print("✅ Pip dependency check passed")
        else:
            print("❌ Pip dependency check failed:")
            print(python_info['pip_check_result']['stderr'])
    
    print()
    
    # Parse requirements
    requirements_file = "requirements.txt"
    if not Path(requirements_file).exists():
        print(f"❌ {requirements_file} not found")
        return
    
    packages = parse_requirements(requirements_file)
    print(f"📦 Found {len(packages)} unique packages in {requirements_file}")
    print()
    
    # Check each package
    results = []
    installed_info = []
    
    print("Checking Python 3.10+ support for each package...")
    print()
    
    for i, package in enumerate(packages, 1):
        print(f"[{i}/{len(packages)}] Checking {package}...", end=" ")
        
        # Check PyPI support
        result = check_package_python_support(package)
        results.append(result)
        
        # Check if installed
        installed = check_with_pip_show(package)
        installed_info.append(installed)
        
        if result['status'] == 'SUPPORTED':
            print("✅ SUPPORTED")
        elif result['status'] == 'NOT_SUPPORTED':
            print("❌ NOT SUPPORTED")
        else:
            print("⚠️  ERROR")
    
    print()
    print("📊 SUMMARY")
    print("=" * 50)
    
    supported = [r for r in results if r['status'] == 'SUPPORTED']
    not_supported = [r for r in results if r['status'] == 'NOT_SUPPORTED']
    errors = [r for r in results if r['status'] == 'ERROR']
    installed = [i for i in installed_info if i['status'] == 'INSTALLED']
    
    print(f"✅ Supported: {len(supported)}")
    print(f"❌ Not Supported: {len(not_supported)}")
    print(f"⚠️  Errors: {len(errors)}")
    print(f"📦 Installed: {len(installed)}")
    print()
    
    if not_supported:
        print("❌ PACKAGES NOT SUPPORTING PYTHON 3.10+:")
        print("-" * 40)
        for result in not_supported:
            print(f"  • {result['package']} (v{result['latest_version']})")
            if result['python_support']:
                print(f"    Supported versions: {', '.join(result['python_support'])}")
            else:
                print(f"    No Python version info available")
        print()
    
    if errors:
        print("⚠️  PACKAGES WITH ERRORS:")
        print("-" * 30)
        for result in errors:
            print(f"  • {result['package']}: {result['error']}")
        print()
    
    if supported:
        print("✅ PACKAGES SUPPORTING PYTHON 3.10+:")
        print("-" * 40)
        for result in supported[:10]:  # Show first 10
            print(f"  • {result['package']} (v{result['latest_version']})")
        if len(supported) > 10:
            print(f"  ... and {len(supported) - 10} more")
    
    print()
    
    # Show installed packages
    if installed:
        print("📦 INSTALLED PACKAGES:")
        print("-" * 25)
        for info in installed[:10]:  # Show first 10
            print(f"  • {info['package']} (v{info['installed_version']})")
        if len(installed) > 10:
            print(f"  ... and {len(installed) - 10} more")
        print()
    
    # Recommendations
    if not_supported:
        print("🔧 RECOMMENDATIONS:")
        print("-" * 20)
        print("1. Update packages to newer versions that support Python 3.10+")
        print("2. Consider alternative packages with Python 3.10+ support")
        print("3. Contact package maintainers for Python 3.10+ support")
        print("4. Use virtual environments to test with Python 3.10+")
        print("5. Check package documentation for Python 3.10+ compatibility")
    else:
        print("🎉 All packages support Python 3.10+!")
    
    # Save detailed results
    report_data = {
        'python_environment': python_info,
        'total_packages': len(packages),
        'supported_count': len(supported),
        'not_supported_count': len(not_supported),
        'error_count': len(errors),
        'installed_count': len(installed),
        'results': results,
        'installed_info': installed_info
    }
    
    with open('python310_support_report_v2.json', 'w') as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: python310_support_report_v2.json")

if __name__ == "__main__":
    main() 