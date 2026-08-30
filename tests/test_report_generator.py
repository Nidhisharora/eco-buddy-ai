"""Tests for asynchronous report generator."""

import pytest
from unittest.mock import MagicMock, patch

from src.reporting.report_generator import ReportGenerator
from src.reporting.report_job_models import ReportInput, ReportType, ReportStatus


class TestReportGenerator:
    """Test asynchronous report generation."""
    
    def test_generate_async_success(self):
        """Test successful async report generation."""
        # Mock the job service
        mock_service = MagicMock()
        mock_service.mark_completed.return_value = True
        
        generator = ReportGenerator(mock_service)
        
        report_input = ReportInput(
            user_id=1,
            report_type=ReportType.MONTHLY,
            metrics_data={'total_emissions': 100.5},
            assessment_data={'eco_score': 75},
            recommendations_data={'key_insight': 'Test insight'}
        )
        
        with patch('src.reporting.report_generator.generate_pdf') as mock_pdf:
            mock_pdf.return_value = '/tmp/test_report.pdf'
            with patch('os.path.getsize', return_value=5120):
                result = generator.generate_async('job_123', report_input)
        
        assert result is True
        mock_service.start_generation.assert_called_once_with('job_123')
        mock_service.mark_completed.assert_called_once()
    
    def test_generate_async_failure(self):
        """Test handling of generation failure."""
        mock_service = MagicMock()
        generator = ReportGenerator(mock_service)
        
        report_input = ReportInput(
            user_id=1,
            report_type=ReportType.MONTHLY
        )
        
        with patch('src.reporting.report_generator.generate_pdf') as mock_pdf:
            mock_pdf.return_value = None  # Simulate PDF generation failure
            result = generator.generate_async('job_123', report_input)
        
        assert result is False
        mock_service.mark_failed.assert_called_once()
        args = mock_service.mark_failed.call_args
        assert args[1]['should_retry'] is True