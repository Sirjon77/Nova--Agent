import pytest
from unittest.mock import Mock, patch
from utils.summarizer import summarize_text, EnhancedSummarizer

class TestSummarizerEnhanced:
    def test_summarize_empty_text(self):
        """Test summarization of empty text."""
        result = summarize_text("", max_length=100)
        assert result == ""

    def test_summarize_short_text(self):
        """Test summarization of text shorter than max_length."""
        text = "This is a short text that doesn't need summarization."
        result = summarize_text(text, max_length=100)
        assert result == text

    def test_summarize_long_text(self):
        """Test summarization of long text."""
        long_text = "This is a very long text. " * 50
        result = summarize_text(long_text, max_length=100)
        assert len(result) <= 100
        assert len(result) < len(long_text)

    def test_summarize_with_specific_max_length(self):
        """Test summarization with specific max_length."""
        text = "This is a test text that should be summarized to exactly 50 characters."
        result = summarize_text(text, max_length=50)
        assert len(result) <= 50

    @patch('utils.summarizer.chat_completion')
    def test_summarize_with_openai_fallback(self, mock_chat):
        """Test summarization when OpenAI is available."""
        mock_chat.return_value = "Summarized content"
        
        text = "This is a long text that needs summarization."
        result = summarize_text(text, max_length=50)
        
        assert result == "Summarized content"
        mock_chat.assert_called_once()

    def test_summarize_without_openai(self):
        """Test summarization when OpenAI is not available."""
        with patch('utils.summarizer.chat_completion', side_effect=ImportError):
            text = "This is a long text that needs summarization."
            result = summarize_text(text, max_length=50)
            
            # Should fall back to simple truncation
            assert len(result) <= 50
            assert result != text

    def test_summarize_with_special_characters(self):
        """Test summarization with special characters."""
        text = "This text contains special chars: @#$%^&*() and emojis: 😀🎉🚀"
        result = summarize_text(text, max_length=30)
        assert len(result) <= 30

    def test_summarize_with_html_content(self):
        """Test summarization with HTML content."""
        html_text = "<p>This is <strong>HTML</strong> content with <a href='#'>links</a>.</p>"
        result = summarize_text(html_text, max_length=50)
        assert len(result) <= 50
        # Should strip HTML tags
        assert "<" not in result
        assert ">" not in result

    def test_summarize_with_multiple_paragraphs(self):
        """Test summarization with multiple paragraphs."""
        text = "First paragraph. Second paragraph. Third paragraph. Fourth paragraph."
        result = summarize_text(text, max_length=30)
        assert len(result) <= 30

    def test_enhanced_summarizer_initialization(self):
        """Test EnhancedSummarizer initialization."""
        summarizer = EnhancedSummarizer()
        assert summarizer is not None

    def test_enhanced_summarizer_with_custom_prompt(self):
        """Test EnhancedSummarizer with custom prompt."""
        summarizer = EnhancedSummarizer()
        text = "This is a test text for summarization."
        
        with patch('utils.summarizer.chat_completion') as mock_chat:
            mock_chat.return_value = "Custom summarized content"
            
            result = summarizer.summarize(text, max_length=50, prompt="Custom prompt")
            assert result == "Custom summarized content"

    def test_summarize_with_different_languages(self):
        """Test summarization with different languages."""
        # English text
        english_text = "This is English text for summarization."
        english_result = summarize_text(english_text, max_length=20)
        assert len(english_result) <= 20
        
        # Spanish text
        spanish_text = "Este es texto en español para resumir."
        spanish_result = summarize_text(spanish_text, max_length=20)
        assert len(spanish_result) <= 20

    def test_summarize_with_numbers_and_dates(self):
        """Test summarization with numbers and dates."""
        text = "The event happened on 2023-12-25. There were 150 participants. The budget was $50,000."
        result = summarize_text(text, max_length=40)
        assert len(result) <= 40
        # Should preserve important numbers
        assert "150" in result or "$50,000" in result

    def test_summarize_with_technical_content(self):
        """Test summarization with technical content."""
        technical_text = """
        The API endpoint /api/v1/users accepts GET requests with query parameters:
        - page: integer (default: 1)
        - limit: integer (default: 10)
        - sort: string (default: 'created_at')
        Returns JSON response with user data.
        """
        result = summarize_text(technical_text, max_length=80)
        assert len(result) <= 80
        assert "API" in result or "endpoint" in result

    def test_summarize_error_handling(self):
        """Test summarization error handling."""
        # Test with None input
        result = summarize_text(None, max_length=50)
        assert result == ""
        
        # Test with non-string input
        result = summarize_text(123, max_length=50)
        assert result == "123"

    def test_summarize_performance(self):
        """Test summarization performance with large text."""
        import time
        
        # Create a large text
        large_text = "This is a sentence. " * 1000
        
        start_time = time.time()
        result = summarize_text(large_text, max_length=100)
        end_time = time.time()
        
        # Should complete within reasonable time (5 seconds)
        assert end_time - start_time < 5
        assert len(result) <= 100 