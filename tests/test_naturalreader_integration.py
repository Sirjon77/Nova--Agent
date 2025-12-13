import pytest
import os
from unittest.mock import Mock, patch
from integrations.naturalreader import synthesize_speech, NaturalReaderError

class TestNaturalReaderIntegration:
    def test_missing_api_key(self):
        """Test that missing API key raises RuntimeError."""
        os.environ.pop("NATURAL_READER_API_KEY", None)
        
        with pytest.raises(RuntimeError, match="NATURAL_READER_API_KEY"):
            synthesize_speech("Hello world")

    def test_missing_voice_id(self):
        """Test that missing voice ID raises RuntimeError."""
        os.environ["NATURAL_READER_API_KEY"] = "test_key"
        os.environ.pop("NATURAL_READER_VOICE_ID", None)
        
        with pytest.raises(RuntimeError, match="voice_id"):
            synthesize_speech("Hello world")  # No voice_id provided

    @patch('integrations.naturalreader.requests.post')
    def test_successful_synthesis(self, mock_post):
        """Test successful speech synthesis."""
        os.environ["NATURAL_READER_API_KEY"] = "test_key"
        os.environ["NATURAL_READER_VOICE_ID"] = "en-US-test"
        
        # Mock successful response with audio content
        mock_post.return_value = Mock(
            status_code=200,
            content=b"fake_audio_content"
        )
        
        with patch('builtins.open', create=True) as mock_open:
            mock_file = Mock()
            mock_open.return_value.__enter__.return_value = mock_file
            
            result = synthesize_speech("Hello world", format="wav")
            
            assert result.endswith(".wav")
            assert os.path.basename(result).startswith("naturalreader_")
            mock_file.write.assert_called_with(b"fake_audio_content")

    @patch('integrations.naturalreader.requests.post')
    def test_api_error(self, mock_post):
        """Test handling of API error."""
        os.environ["NATURAL_READER_API_KEY"] = "test_key"
        os.environ["NATURAL_READER_VOICE_ID"] = "en-US-test"
        
        # Mock API error
        mock_post.return_value = Mock(
            status_code=400,
            text="Bad Request"
        )
        
        with pytest.raises(NaturalReaderError, match="Bad Request"):
            synthesize_speech("Hello world")

    @patch('integrations.naturalreader.requests.post')
    def test_network_error(self, mock_post):
        """Test handling of network error."""
        os.environ["NATURAL_READER_API_KEY"] = "test_key"
        os.environ["NATURAL_READER_VOICE_ID"] = "en-US-test"
        
        # Mock network error
        mock_post.side_effect = Exception("Network error")
        
        with pytest.raises(NaturalReaderError, match="Network error"):
            synthesize_speech("Hello world")

    @patch('integrations.naturalreader.requests.post')
    def test_different_output_formats(self, mock_post):
        """Test synthesis with different output formats."""
        os.environ["NATURAL_READER_API_KEY"] = "test_key"
        os.environ["NATURAL_READER_VOICE_ID"] = "en-US-test"
        
        mock_post.return_value = Mock(
            status_code=200,
            content=b"fake_audio_content"
        )
        
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.write = Mock()
            
            # Test different formats
            result_wav = synthesize_speech("Hello", format="wav")
            result_mp3 = synthesize_speech("Hello", format="mp3")
            
            assert result_wav.endswith(".wav")
            assert result_mp3.endswith(".mp3")

    def test_voice_id_parameter_override(self):
        """Test that voice_id parameter overrides environment variable."""
        os.environ["NATURAL_READER_API_KEY"] = "test_key"
        os.environ["NATURAL_READER_VOICE_ID"] = "env_voice"
        
        with patch('integrations.naturalreader.requests.post') as mock_post:
            mock_post.return_value = Mock(
                status_code=200,
                content=b"fake_audio_content"
            )
            
            with patch('builtins.open', create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.write = Mock()
                
                # Should use parameter voice_id, not environment
                synthesize_speech("Hello", voice_id="param_voice")
                
                # Verify the correct voice_id was used in the request
                call_args = mock_post.call_args
                assert "param_voice" in str(call_args) 