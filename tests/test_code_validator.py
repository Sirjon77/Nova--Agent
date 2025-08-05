import pytest
import tempfile
import os
from utils.code_validator import CodeValidator

class TestCodeValidator:
    def test_initialization(self):
        """Test CodeValidator class initialization."""
        validator = CodeValidator()
        assert validator is not None

    def test_validate_syntax_valid_code(self):
        """Test syntax validation with valid Python code."""
        validator = CodeValidator()
        result = validator.validate_syntax("def test(): return True")
        assert result.is_valid is True
        assert result.error_message is None

    def test_validate_syntax_invalid_code(self):
        """Test syntax validation with invalid Python code."""
        validator = CodeValidator()
        result = validator.validate_syntax("def test(: return True")  # Missing closing paren
        assert result.is_valid is False
        assert "SyntaxError" in result.error_message

    def test_validate_imports_valid(self):
        """Test import validation with valid imports."""
        validator = CodeValidator()
        result = validator.validate_imports("import os\nimport sys")
        assert result.is_valid is True

    def test_validate_imports_invalid(self):
        """Test import validation with invalid imports."""
        validator = CodeValidator()
        result = validator.validate_imports("import nonexistent_module")
        assert result.is_valid is False

    def test_safe_execute_valid(self):
        """Test safe execution with valid code."""
        validator = CodeValidator()
        result = validator.safe_execute("x = 1 + 1")
        assert result.is_valid is True
        assert result.result == 2

    def test_safe_execute_invalid(self):
        """Test safe execution with invalid code."""
        validator = CodeValidator()
        result = validator.safe_execute("x = 1 / 0")
        assert result.is_valid is False
        assert "ZeroDivisionError" in result.error_message

    def test_get_suggestions(self):
        """Test code improvement suggestions."""
        validator = CodeValidator()
        suggestions = validator.get_suggestions("x=1+1")  # Missing spaces
        assert len(suggestions) > 0
        assert any("spaces" in suggestion.lower() for suggestion in suggestions)

    def test_fix_common_issues(self):
        """Test automatic fixing of common issues."""
        validator = CodeValidator()
        fixed_code = validator.fix_common_issues("x=1+1")
        assert "x = 1 + 1" in fixed_code  # Should add spaces 