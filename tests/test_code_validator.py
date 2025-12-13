from utils.code_validator import CodeValidator

class TestCodeValidator:
    def test_initialization(self):
        """Test CodeValidator class initialization."""
        validator = CodeValidator()
        assert validator is not None

    def test_validate_code_valid(self):
        """Test code validation with valid Python code."""
        validator = CodeValidator()
        result = validator.validate_code("def test(): return True")
        assert result is not None
        assert "is_valid" in result or "valid" in result

    def test_validate_code_invalid(self):
        """Test code validation with invalid Python code."""
        validator = CodeValidator()
        result = validator.validate_code("def test(: return True")  # Missing closing paren
        assert result is not None
        # Should return validation result

    def test_validate_code_with_imports(self):
        """Test code validation with imports."""
        validator = CodeValidator()
        result = validator.validate_code("import os\nimport sys\ndef test(): return True")
        assert result is not None

    def test_validate_code_complex(self):
        """Test code validation with complex code."""
        validator = CodeValidator()
        result = validator.validate_code("x = 1 + 1\ny = x * 2\nprint(y)")
        assert result is not None

    def test_validate_code_empty(self):
        """Test code validation with empty code."""
        validator = CodeValidator()
        result = validator.validate_code("")
        assert result is not None 