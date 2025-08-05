import pytest
import os
import tempfile
from unittest.mock import Mock, patch
from integrations.murf import synthesize_speech, MurfError

class TestMurfIntegration:
    def test_missing_api_key(self):
        """Test that missing API key raises RuntimeError."""
        # Clear environment variables
        os.environ.pop("MURF_API_KEY", None)
        os.environ.pop("MURF_PROJECT_ID", None)
        
        with pytest.raises(RuntimeError, match="MURF_API_KEY"):
            synthesize_speech("Hello world")

    def test_missing_project_id(self):
        """Test that missing project ID raises RuntimeError."""
        os.environ["MURF_API_KEY"] = "test_key"
        os.environ.pop("MURF_PROJECT_ID", None)
        
        with pytest.raises(RuntimeError, match="MURF_PROJECT_ID"):
            synthesize_speech("Hello world")

    @patch('integrations.murf.requests.post')
    def test_successful_synthesis(self, mock_post):
        """Test successful speech synthesis."""
        os.environ["MURF_API_KEY"] = "test_key"
        os.environ["MURF_PROJECT_ID"] = "test_project"
        os.environ["MURF_VOICE_ID"] = "en-US-test"
        
        # Mock successful job creation
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {"jobId": "test_job_123"}
        )
        
        with patch('integrations.murf.requests.get') as mock_get:
            # Mock status polling
            mock_get.side_effect = [
                Mock(status_code=200, json=lambda: {"status": "pending"}),
                Mock(status_code=200, json=lambda: {"status": "completed"})
            ]
            
            with patch('builtins.open', create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.write = Mock()
                
                result = synthesize_speech("Hello world", format="mp3")
                
                assert result.endswith(".mp3")
                assert os.path.basename(result).startswith("murf_")

    @patch('integrations.murf.requests.post')
    def test_api_error_job_creation(self, mock_post):
        """Test handling of API error during job creation."""
        os.environ["MURF_API_KEY"] = "test_key"
        os.environ["MURF_PROJECT_ID"] = "test_project"
        os.environ["MURF_VOICE_ID"] = "en-US-test"
        
        # Mock API error
        mock_post.return_value = Mock(
            status_code=400,
            text="Bad Request"
        )
        
        with pytest.raises(MurfError, match="Bad Request"):
            synthesize_speech("Hello world")

    @patch('integrations.murf.requests.post')
    @patch('integrations.murf.requests.get')
    def test_api_error_status_polling(self, mock_get, mock_post):
        """Test handling of API error during status polling."""
        os.environ["MURF_API_KEY"] = "test_key"
        os.environ["MURF_PROJECT_ID"] = "test_project"
        os.environ["MURF_VOICE_ID"] = "en-US-test"
        
        # Mock successful job creation
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {"jobId": "test_job_123"}
        )
        
        # Mock status polling error
        mock_get.return_value = Mock(
            status_code=500,
            text="Internal Server Error"
        )
        
        with pytest.raises(MurfError, match="Internal Server Error"):
            synthesize_speech("Hello world")

    @patch('integrations.murf.requests.post')
    @patch('integrations.murf.requests.get')
    def test_timeout_handling(self, mock_get, mock_post):
        """Test handling of timeout during synthesis."""
        os.environ["MURF_API_KEY"] = "test_key"
        os.environ["MURF_PROJECT_ID"] = "test_project"
        os.environ["MURF_VOICE_ID"] = "en-US-test"
        
        # Mock successful job creation
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {"jobId": "test_job_123"}
        )
        
        # Mock status polling that never completes
        mock_get.return_value = Mock(
            status_code=200,
            json=lambda: {"status": "pending"}
        )
        
        with pytest.raises(MurfError, match="timeout"):
            synthesize_speech("Hello world", timeout=1)

    def test_invalid_voice_id(self):
        """Test that invalid voice ID raises RuntimeError."""
        os.environ["MURF_API_KEY"] = "test_key"
        os.environ["MURF_PROJECT_ID"] = "test_project"
        os.environ.pop("MURF_VOICE_ID", None)
        
        with pytest.raises(RuntimeError, match="voice_id"):
            synthesize_speech("Hello world")  # No voice_id provided

    @patch('integrations.murf.requests.post')
    def test_different_output_formats(self, mock_post):
        """Test synthesis with different output formats."""
        os.environ["MURF_API_KEY"] = "test_key"
        os.environ["MURF_PROJECT_ID"] = "test_project"
        os.environ["MURF_VOICE_ID"] = "en-US-test"
        
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {"jobId": "test_job_123"}
        )
        
        with patch('integrations.murf.requests.get') as mock_get:
            mock_get.side_effect = [
                Mock(status_code=200, json=lambda: {"status": "completed"})
            ]
            
            with patch('builtins.open', create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.write = Mock()
                
                # Test different formats
                result_wav = synthesize_speech("Hello", format="wav")
                result_mp3 = synthesize_speech("Hello", format="mp3")
                
                assert result_wav.endswith(".wav")
                assert result_mp3.endswith(".mp3") 