"""
Integration tests to verify that all OpenAI calls use the model registry.
This ensures no invalid model names can reach the OpenAI API.
"""

import pytest
import ast
import os
from pathlib import Path
from typing import List, Tuple

def find_openai_calls_in_file(file_path: str) -> List[Tuple[int, str]]:
    """
    Find all openai.ChatCompletion.create calls in a Python file.
    
    Returns:
        List of (line_number, line_content) tuples
    """
    calls = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for line_num, line in enumerate(lines, 1):
            if 'openai.ChatCompletion.create' in line:
                calls.append((line_num, line.strip()))
                
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        
    return calls

def find_python_files_with_openai_calls() -> List[str]:
    """
    Find all Python files that contain OpenAI API calls.
    
    Returns:
        List of file paths
    """
    files_with_calls = []
    
    # Directories to search
    search_dirs = [
        '.',
        'utils',
        'nova',
        'nova_core',
        'backend',
        'agents'
    ]
    
    for search_dir in search_dirs:
        if not os.path.exists(search_dir):
            continue
            
        for root, dirs, files in os.walk(search_dir):
            # Skip test directories and __pycache__
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    calls = find_openai_calls_in_file(file_path)
                    if calls:
                        files_with_calls.append(file_path)
                        
    return files_with_calls

def check_file_uses_model_registry(file_path: str) -> Tuple[bool, List[str]]:
    """
    Check if a file properly uses the model registry.
    
    Returns:
        (is_compliant, list_of_issues)
    """
    issues = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check if file uses the wrapper approach (preferred) or direct model registry
        uses_wrapper = 'from nova.services.openai_client import chat_completion' in content
        uses_direct_registry = 'from nova_core.model_registry import' in content
        
        if not uses_wrapper and not uses_direct_registry:
            issues.append("Missing model registry import or OpenAI wrapper import")
            
        # Check if file has fallback import (for wrapper approach)
        if uses_wrapper and 'except ImportError:' not in content:
            issues.append("Missing fallback for OpenAI wrapper import")
            
        # Find all openai.ChatCompletion.create calls
        calls = find_openai_calls_in_file(file_path)
        
        for line_num, line in calls:
            # Check if the call uses a resolved model variable
            if 'model=' in line:
                # Look for patterns that indicate model registry usage
                if 'resolve_model(' in line or 'resolve(' in line:
                    continue  # This is good
                elif 'model=' in line and ('"gpt-' in line or "'gpt-" in line):
                    # Check if this is in a fallback function (which is OK)
                    if 'def chat_completion(' in content and 'return openai.ChatCompletion.create' in content:
                        continue  # This is a fallback function, which is OK
                    issues.append(f"Line {line_num}: Direct model string in OpenAI call")
                elif 'model=' in line and 'DEFAULT_MODEL' in line:
                    # Check if DEFAULT_MODEL is properly resolved
                    if 'resolve_model(DEFAULT_MODEL)' not in content:
                        issues.append(f"Line {line_num}: DEFAULT_MODEL not resolved through registry")
                        
    except Exception as e:
        issues.append(f"Error analyzing file: {e}")
        
    return len(issues) == 0, issues

class TestModelRegistryIntegration:
    """Test that all OpenAI calls use the model registry."""
    
    def test_all_openai_calls_use_registry(self):
        """Verify that all files with OpenAI calls use the model registry."""
        files_with_calls = find_python_files_with_openai_calls()
        
        assert len(files_with_calls) > 0, "No files with OpenAI calls found"
        
        non_compliant_files = []
        
        for file_path in files_with_calls:
            is_compliant, issues = check_file_uses_model_registry(file_path)
            if not is_compliant:
                non_compliant_files.append((file_path, issues))
                
        if non_compliant_files:
            error_msg = "Files found that don't use model registry:\n"
            for file_path, issues in non_compliant_files:
                error_msg += f"\n{file_path}:\n"
                for issue in issues:
                    error_msg += f"  - {issue}\n"
            pytest.fail(error_msg)
    
    def test_model_registry_imports(self):
        """Test that model registry can be imported."""
        try:
            from nova_core.model_registry import resolve, get_default_model
            assert callable(resolve)
            assert callable(get_default_model)
        except ImportError as e:
            pytest.fail(f"Failed to import model registry: {e}")
    
    def test_resolve_function_works(self):
        """Test that the resolve function works correctly."""
        from nova_core.model_registry import resolve
        
        # Test valid aliases that are actually in our registry
        assert resolve("gpt-4o-mini") == "gpt-4o"
        assert resolve("gpt-4o-vision") == "gpt-4o"
        assert resolve("o3") == "gpt-3.5-turbo"
        assert resolve("o3-pro") == "gpt-4o"
        
        # Test that unknown aliases are passed through (not raised as KeyError)
        assert resolve("invalid-model") == "invalid-model"
    
    def test_no_hardcoded_model_names(self):
        """Test that no Python files contain hardcoded invalid model names in code (not comments)."""
        invalid_models = [
            "gpt-4o-mini-search",
            "gpt-4o-mini-TTS",
        ]
        
        files_with_invalid_models = []
        
        for root, dirs, files in os.walk('.'):
            # Skip test directories and __pycache__
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    
                    # Skip model registry and test files
                    if 'model_registry.py' in file_path or 'test_' in file_path:
                        continue
                        
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            
                        for line_num, line in enumerate(lines, 1):
                            # Skip comment lines and docstrings
                            stripped_line = line.strip()
                            if stripped_line.startswith('#') or stripped_line.startswith('"""') or stripped_line.startswith("'''"):
                                continue
                                
                            # Check for invalid models in actual code
                            for invalid_model in invalid_models:
                                if invalid_model in line and not line.strip().startswith('#'):
                                    # Check if it's in a comment within the line
                                    comment_pos = line.find('#')
                                    if comment_pos == -1 or line.find(invalid_model) < comment_pos:
                                        files_with_invalid_models.append((file_path, invalid_model, line_num))
                                        break
                                        
                    except Exception:
                        continue  # Skip files we can't read
                        
        if files_with_invalid_models:
            error_msg = "Files found with hardcoded invalid model names in code:\n"
            for file_path, invalid_model, line_num in files_with_invalid_models:
                error_msg += f"  {file_path}:{line_num}: {invalid_model}\n"
            pytest.fail(error_msg)

if __name__ == "__main__":
    pytest.main([__file__]) 