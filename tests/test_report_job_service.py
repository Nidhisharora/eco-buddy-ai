"""Tests for report job service."""

import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models import Base, ReportJob, User
from src.reporting.report_job_models import (
    ReportInput, ReportStatus, ReportType
)
from src.reporting.report_job_service import ReportJobService


@pytest.fixture
def db_session():
    """Create in-memory SQLite database for testing."""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def test_user(db_session):
    """Create test user."""
    user = User(username="testuser", email="test@example.com")
    db_session.add(user)
    db_session.commit()
    return user


class TestReportJobService:
    """Test report job lifecycle management."""
    
    def test_create_job(self, db_session, test_user):
        """Test creating a new report job."""
        service = ReportJobService(db_session)
        report_input = ReportInput(
            user_id=test_user.id,
            report_type=ReportType.MONTHLY,
            assessment_data={'eco_score': 75}
        )
        
        job_id = service.create_job(
            user_id=test_user.id,
            report_type=ReportType.MONTHLY,
            report_input=report_input
        )
        
        assert job_id is not None
        status = service.get_status(job_id)
        assert status.status == ReportStatus.PENDING
        assert status.user_id == test_user.id
    
    def test_duplicate_request_deduplication(self, db_session, test_user):
        """Test that duplicate requests reuse same job."""
        service = ReportJobService(db_session)
        report_input = ReportInput(
            user_id=test_user.id,
            report_type=ReportType.MONTHLY,
            assessment_data={'eco_score': 75}
        )
        
        job_id_1 = service.create_job(
            user_id=test_user.id,
            report_type=ReportType.MONTHLY,
            report_input=report_input
        )
        
        job_id_2 = service.create_job(
            user_id=test_user.id,
            report_type=ReportType.MONTHLY,
            report_input=report_input
        )
        
        assert job_id_1 == job_id_2
    
    def test_mark_completed(self, db_session, test_user):
        """Test marking job as completed."""
        service = ReportJobService(db_session)
        report_input = ReportInput(
            user_id=test_user.id,
            report_type=ReportType.MONTHLY
        )
        
        job_id = service.create_job(
            user_id=test_user.id,
            report_type=ReportType.MONTHLY,
            report_input=report_input
        )
        
        service.start_generation(job_id)
        success = service.mark_completed(job_id, "/tmp/report.pdf", 1024)
        
        assert success
        status = service.get_status(job_id)
        assert status.status == ReportStatus.COMPLETED
        assert status.artifact is not None
        assert status.artifact.path == "/tmp/report.pdf"
    
    def test_mark_failed_with_retry(self, db_session, test_user):
        """Test marking job as failed with retry scheduling."""
        service = ReportJobService(db_session)
        report_input = ReportInput(
            user_id=test_user.id,
            report_type=ReportType.MONTHLY
        )
        
        job_id = service.create_job(
            user_id=test_user.id,
            report_type=ReportType.MONTHLY,
            report_input=report_input
        )
        
        service.mark_failed(job_id, "Test error", should_retry=True)
        
        status = service.get_status(job_id)
        assert status.status == ReportStatus.RETRYING
        assert status.retry_count == 1
        assert status.next_retry_at is not None
    
    def test_permanent_failure_after_max_retries(self, db_session, test_user):
        """Test job marked as failed after max retries exceeded."""
        service = ReportJobService(db_session)
        report_input = ReportInput(
            user_id=test_user.id,
            report_type=ReportType.MONTHLY
        )
        
        job_id = service.create_job(
            user_id=test_user.id,
            report_type=ReportType.MONTHLY,
            report_input=report_input
        )
        
        # Exhaust retries
        for i in range(3):
            service.mark_failed(job_id, f"Error {i}", should_retry=True)
        
        service.mark_failed(job_id, "Final error", should_retry=True)
        
        status = service.get_status(job_id)
        assert status.status == ReportStatus.FAILED
        assert status.retry_count == 3