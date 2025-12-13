#!/usr/bin/env python3
"""
Script to fix common linting issues in the Nova Agent codebase.
This addresses the issues found by ruff and black.
"""

import subprocess
import sys
import os

def run_command(cmd):
    """Run a command and return its output."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
    return result.returncode == 0

def main():
    """Main function to fix linting issues."""
    print("Nova Agent Linting Fix Script")
    print("=" * 50)
    
    # Check if we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("Warning: Not in a virtual environment. Consider activating one first.")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Step 1: Run ruff with auto-fix
    print("\n1. Running ruff auto-fix...")
    if run_command("ruff check . --fix --unsafe-fixes"):
        print("✓ Ruff auto-fix completed")
    else:
        print("✗ Ruff auto-fix had issues")
    
    # Step 2: Run black formatter
    print("\n2. Running black formatter...")
    if run_command("black ."):
        print("✓ Black formatting completed")
    else:
        print("✗ Black formatting had issues")
    
    # Step 3: Show remaining issues
    print("\n3. Checking remaining issues...")
    
    print("\nRemaining ruff issues:")
    subprocess.run("ruff check . | head -20", shell=True)
    
    print("\nRemaining mypy issues:")
    subprocess.run("mypy . 2>&1 | head -20", shell=True)
    
    print("\n" + "=" * 50)
    print("Linting fix completed!")
    print("\nNext steps:")
    print("1. Review the changes made by the tools")
    print("2. Fix any remaining issues manually")
    print("3. Run 'pytest' to ensure tests still pass")
    print("4. Commit the changes")

if __name__ == "__main__":
    main()
