"""Tests for audio transcription and brief generation."""
import pytest
from unittest.mock import patch, MagicMock, mock_open
from pipeline.content.audio_to_brief import transcribe_audio


class TestTranscribeAudio:
    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError, match="not found"):
            transcribe_audio("/nonexistent/file.mp3")

    @patch("pipeline.content.audio_to_brief.Path")
    def test_file_too_large(self, mock_path_cls):
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.stat.return_value = MagicMock(st_size=30 * 1024 * 1024)
        mock_path_cls.return_value = mock_path
        with pytest.raises(ValueError, match="exceeds Whisper"):
            transcribe_audio("too_large.mp3")

    @patch("pipeline.content.audio_to_brief.OpenAI")
    @patch("pipeline.content.audio_to_brief.Path")
    @patch("builtins.open", mock_open(read_data=b"fake audio"))
    def test_successful_transcription(self, mock_path_cls, mock_openai_cls):
        mock_path = MagicMock()
        mock_path.exists.return_value = True
        mock_path.stat.return_value = MagicMock(st_size=5 * 1024 * 1024)
        mock_path_cls.return_value = mock_path
        mock_client = MagicMock()
        mock_client.audio.transcriptions.create.return_value = "SPY is testing the 50 day."
        mock_openai_cls.return_value = mock_client
        result = transcribe_audio("premarket.mp3", api_key="test-key")
        assert "SPY" in result
