"""
Code Validation System for Nova Agent Self-Coder

This module provides code validation and testing capabilities:
- Syntax validation
- Import testing
- Code execution testing
- Error reporting and suggestions
"""

import ast
import subprocess
import tempfile
import os
import logging
from typing import Dict, Any, List, Optional, Tuple
from utils.user_feedback import feedback_manager

logger = logging.getLogger(__name__)

class CodeValidator:
    """
    Validates and tests generated code for correctness.
    
    Features:
    - Syntax validation
    - Import testing
    - Safe execution testing
    - Error reporting
    - Code improvement suggestions
    """
    
    def __init__(self, sandbox_dir: Optional[str] = None):
        """
        Initialize the code validator.
        
        Args:
            sandbox_dir: Directory for safe code execution (optional)
        """
        self.sandbox_dir = sandbox_dir or tempfile.mkdtemp(prefix="nova_code_")
        logger.info(f"CodeValidator initialized with sandbox: {self.sandbox_dir}")
    
    def validate_code(self, code: str, filename: str = "generated_code.py") -> Dict[str, Any]:
        """
        Validate generated code for syntax and basic correctness.
        
        Args:
            code: Python code to validate
            filename: Filename for context
            
        Returns:
            Dict containing validation results
        """
        result = {
            "valid": False,
            "syntax_valid": False,
            "imports_valid": False,
            "executable": False,
            "errors": [],
            "warnings": [],
            "suggestions": []
        }
        
        try:
            # Step 1: Syntax validation
            syntax_result = self._validate_syntax(code)
            result["syntax_valid"] = syntax_result["valid"]
            result["errors"].extend(syntax_result["errors"])
            
            if not syntax_result["valid"]:
                result["suggestions"].append("Fix syntax errors before proceeding")
                return result
            
            # Step 2: Import validation
            import_result = self._validate_imports(code)
            result["imports_valid"] = import_result["valid"]
            result["warnings"].extend(import_result["warnings"])
            
            # Step 3: Basic execution test
            execution_result = self._test_execution(code)
            result["executable"] = execution_result["valid"]
            result["errors"].extend(execution_result["errors"])
            
            # Overall validation result
            result["valid"] = (result["syntax_valid"] and 
                             result["imports_valid"] and 
                             result["executable"])
            
            # Add success message if valid
            if result["valid"]:
                result["suggestions"].append("Code validation successful! The generated code is ready to use.")
            
            logger.info(f"Code validation completed for {filename}: {result['valid']}")
            return result
            
        except Exception as e:
            logger.error(f"Code validation failed: {e}")
            result["errors"].append(f"Validation process failed: {str(e)}")
            return result
    
    def _validate_syntax(self, code: str) -> Dict[str, Any]:
        """
        Validate Python syntax using ast module.
        
        Args:
            code: Python code to validate
            
        Returns:
            Dict containing syntax validation results
        """
        result = {"valid": False, "errors": []}
        
        try:
            ast.parse(code)
            result["valid"] = True
            return result
        except SyntaxError as e:
            result["errors"].append(f"Syntax error: {e.msg} at line {e.lineno}")
            return result
        except Exception as e:
            result["errors"].append(f"Syntax validation failed: {str(e)}")
            return result
    
    def _validate_imports(self, code: str) -> Dict[str, Any]:
        """
        Validate imports in the code.
        
        Args:
            code: Python code to validate
            
        Returns:
            Dict containing import validation results
        """
        result = {"valid": True, "warnings": []}
        
        try:
            tree = ast.parse(code)
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        imports.append(f"{module}.{alias.name}")
            
            # Check for potentially problematic imports
            for imp in imports:
                if imp.startswith("os.") or imp.startswith("sys."):
                    result["warnings"].append(f"Import '{imp}' might have security implications")
                elif imp.startswith("subprocess"):
                    result["warnings"].append(f"Import '{imp}' allows system command execution")
                elif imp.startswith("eval") or imp.startswith("exec"):
                    result["warnings"].append(f"Import '{imp}' allows code execution")
            
            return result
            
        except Exception as e:
            result["valid"] = False
            result["warnings"].append(f"Import validation failed: {str(e)}")
            return result
    
    def _test_execution(self, code: str) -> Dict[str, Any]:
        """
        Test code execution in a safe environment.
        
        Args:
            code: Python code to test
            
        Returns:
            Dict containing execution test results
        """
        result = {"valid": False, "errors": []}
        
        try:
            # Create a temporary file for testing
            test_file = os.path.join(self.sandbox_dir, "test_execution.py")
            
            # Wrap code in a safe execution environment
            safe_code = f"""
import sys
import traceback

def test_execution():
    try:
{chr(10).join('        ' + line for line in code.split(chr(10)))}
        return True
    except Exception as e:
        print(f"Execution error: {{e}}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_execution()
    sys.exit(0 if success else 1)
"""
            
            with open(test_file, 'w') as f:
                f.write(safe_code)
            
            # Run the code with timeout
            process = subprocess.run(
                [sys.executable, test_file],
                capture_output=True,
                text=True,
                timeout=10,  # 10 second timeout
                cwd=self.sandbox_dir
            )
            
            if process.returncode == 0:
                result["valid"] = True
            else:
                result["errors"].append(f"Execution failed: {process.stderr}")
            
            # Clean up
            try:
                os.remove(test_file)
            except:
                pass
            
            return result
            
        except subprocess.TimeoutExpired:
            result["errors"].append("Code execution timed out (possible infinite loop)")
            return result
        except Exception as e:
            result["errors"].append(f"Execution test failed: {str(e)}")
            return result
    
    def suggest_improvements(self, code: str, validation_result: Dict[str, Any]) -> List[str]:
        """
        Suggest improvements based on validation results.
        
        Args:
            code: Original code
            validation_result: Results from validate_code
            
        Returns:
            List of improvement suggestions
        """
        suggestions = []
        
        # Add suggestions based on validation results
        if not validation_result["syntax_valid"]:
            suggestions.append("Fix syntax errors in the generated code")
        
        if validation_result["warnings"]:
            suggestions.append("Review security implications of imports")
        
        if not validation_result["executable"]:
            suggestions.append("Test the code manually to identify runtime issues")
        
        # Add general suggestions
        suggestions.extend([
            "Add error handling to make the code more robust",
            "Include docstrings for better documentation",
            "Add type hints for better code clarity",
            "Consider adding unit tests for the generated code"
        ])
        
        return suggestions
    
    def fix_common_issues(self, code: str) -> Tuple[str, List[str]]:
        """
        Attempt to fix common code issues automatically.
        
        Args:
            code: Code to fix
            
        Returns:
            Tuple of (fixed_code, list_of_fixes_applied)
        """
        fixes_applied = []
        fixed_code = code
        
        # Fix common indentation issues
        if "IndentationError" in code or "TabError" in code:
            # Convert tabs to spaces
            fixed_code = fixed_code.expandtabs(4)
            fixes_applied.append("Fixed indentation (converted tabs to spaces)")
        
        # Fix common import issues
        if "ImportError" in code:
            # Add common imports
            common_imports = [
                "import os",
                "import sys",
                "import logging",
                "from typing import Dict, List, Optional, Any"
            ]
            
            # Check if imports are missing
            for imp in common_imports:
                if imp not in fixed_code:
                    fixed_code = f"{imp}\n{fixed_code}"
                    fixes_applied.append(f"Added missing import: {imp}")
        
        # Fix common syntax issues
        if "SyntaxError" in code:
            # Try to fix common syntax errors
            if "print" in code and "(" not in code.split("print")[1][:10]:
                # Fix print statements for Python 3
                fixed_code = fixed_code.replace("print ", "print(")
                fixed_code = fixed_code.replace("\nprint(", "\nprint(")
                # Add closing parentheses where needed
                lines = fixed_code.split("\n")
                for i, line in enumerate(lines):
                    if line.strip().startswith("print(") and not line.strip().endswith(")"):
                        lines[i] = line + ")"
                fixed_code = "\n".join(lines)
                fixes_applied.append("Fixed print statements for Python 3 compatibility")
        
        return fixed_code, fixes_applied

# Global code validator instance
code_validator = CodeValidator()

# Convenience functions
def validate_code(code: str, filename: str = "generated_code.py") -> Dict[str, Any]:
    """Validate generated code for correctness."""
    return code_validator.validate_code(code, filename)

def suggest_improvements(code: str, validation_result: Dict[str, Any]) -> List[str]:
    """Suggest improvements based on validation results."""
    return code_validator.suggest_improvements(code, validation_result)

def fix_common_issues(code: str) -> Tuple[str, List[str]]:
    """Attempt to fix common code issues automatically."""
    return code_validator.fix_common_issues(code) 