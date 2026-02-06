"""Integration test for error generation workflow.

Tests the complete flow from error generation request to message output.
"""

import pytest
from unittest.mock import Mock, patch

from src.agents.error_generator import ErrorGeneratorAgent
from src.models.error_message import ErrorGenerationRequest, ErrorMessage
from src.services.message_sender import MessageSenderService


class TestErrorGenerationWorkflow:
    """Integration tests for error generation workflow."""
    
    @pytest.fixture
    def error_agent(self, tmp_path):
        """Create error generator agent with sample log."""
        # Create sample log file
        log_file = tmp_path / "test_messages.log"
        log_file.write_text(
            "01/15/24-10:23:45:123 (1234) 2 [License] License key expires in 30 days\n"
            "01/15/24-10:24:10:456 (5678) 1 [Config] Invalid config parameter: globals\n"
        )
        
        return ErrorGeneratorAgent(log_samples_path=log_file)
    
    @pytest.fixture
    def message_sender(self):
        """Create message sender service."""
        return MessageSenderService(output_endpoint="http://localhost:8080/api/messages")
    
    @patch("src.utils.llm_client.LLMClient.parse")
    def test_generation_with_mock_llm(self, mock_parse, error_agent):
        """Test error generation with mocked LLM response."""
        # Mock LLM response
        mock_error = ErrorMessage(
            timestamp="01/15/24-10:30:00:000",
            process_id=9999,
            severity=2,
            category="[TestCat]",
            message_text="Test error message from LLM"
        )
        mock_parse.return_value = mock_error
        
        # Generate error
        request = ErrorGenerationRequest(error_category="license", severity=2)
        result = error_agent.generate_error(request)
        
        # Verify result
        assert isinstance(result, ErrorMessage)
        assert result.severity == 2
        assert result.category == "[TestCat]"
        assert "Test error message" in result.message_text
        
        # Verify LLM was called
        mock_parse.assert_called_once()
    
    def test_generation_with_template_fallback(self, error_agent):
        """Test error generation using template fallback."""
        # Patch LLM client to fail
        with patch("src.agents.error_generator.LLMClient") as mock_client:
            mock_client.return_value.parse.side_effect = Exception("LLM unavailable")
            
            # Should fall back to templates
            request = ErrorGenerationRequest(error_category="config", severity=1)
            result = error_agent.generate_error(request)
            
            # Verify result
            assert isinstance(result, ErrorMessage)
            assert result.severity == 1
            assert result.category in ["[Config]", "[Startup]", "[SystemConfig]"]
    
    def test_all_error_categories(self, error_agent):
        """Test generation for all supported categories."""
        categories = ["config", "license", "os", "journal"]
        
        for category in categories:
            request = ErrorGenerationRequest(error_category=category, severity=2)
            result = error_agent.generate_error(request)
            
            assert isinstance(result, ErrorMessage)
            assert result.severity == 2
            assert len(result.message_text) >= 10  # Has meaningful content
    
    @patch("requests.post")
    def test_end_to_end_generation_to_output(self, mock_post, error_agent, message_sender):
        """Test complete flow from generation to external transmission."""
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "received"}
        mock_post.return_value = mock_response
        
        # Generate error
        request = ErrorGenerationRequest(error_category="license", severity=2)
        error = error_agent.generate_error(request)
        
        # Send to external system
        result = message_sender.send_message(error)
        
        # Verify send was successful
        assert result["status"] == "sent"
        assert not result["queued"]
        
        # Verify HTTP call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "json" in call_args.kwargs
        assert "log_format" in call_args.kwargs["json"]
    
    @patch("requests.post")
    def test_output_failure_with_queueing(self, mock_post, error_agent, message_sender):
        """Test message queueing when endpoint unavailable."""
        # Mock failed HTTP response
        mock_post.side_effect = Exception("Connection refused")
        
        # Generate error
        request = ErrorGenerationRequest(error_category="config", severity=1)
        error = error_agent.generate_error(request)
        
        # Attempt to send
        result = message_sender.send_message(error)
        
        # Verify message was queued
        assert result["status"] == "queued"
        assert result["queued"]
        assert message_sender.get_queue_size() == 1
    
    def test_severity_levels(self, error_agent):
        """Test error generation with different severity levels."""
        for severity in [0, 1, 2, 3]:
            request = ErrorGenerationRequest(error_category="license", severity=severity)
            result = error_agent.generate_error(request)
            
            assert result.severity == severity
    
    def test_agent_observability(self, error_agent):
        """Test that agent tracks statistics."""
        # Generate multiple errors
        for _ in range(3):
            request = ErrorGenerationRequest(error_category="license", severity=2)
            error_agent.generate_error(request)
        
        # Check stats
        stats = error_agent.get_stats()
        assert stats["total_executions"] == 3
        assert stats["total_failures"] == 0
