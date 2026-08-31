"""Service for managing report job lifecycle."""

import hashlib
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session
from src.models import ReportJob
from src.reporting.report_job_models import (
    ReportInput, ReportJobStatus, ReportStatus, ReportType, ReportArtifact
)


logger = logging.getLogger(__name__)


class ReportJobService:
    """Manage report generation jobs in database."""
    
    REPORT_VERSION = "1.0"  # Increment when report logic changes
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def create_job(
        self, 
        user_id: int,
        report_type: ReportType,
        report_input: ReportInput
    ) -> str:
        """Create new report job and return job ID."""
        job_id = str(uuid.uuid4())
        
        # Generate deduplication hash from inputs
        dedup_hash = self._compute_input_hash(user_id, report_type, report_input)
        
        # Check for existing pending/completed job with same inputs
        existing = self.db.query(ReportJob).filter(
            ReportJob.user_id == user_id,
            ReportJob.report_type == report_type.value,
            ReportJob.status.in_(['pending', 'running', 'completed']),
        ).first()
        
        if existing:
            logger.info(f"Found existing job {existing.id} for same report request")
            return existing.id
        
        # Create new job
        job = ReportJob(
            id=job_id,
            user_id=user_id,
            report_type=report_type.value,
            status=ReportStatus.PENDING.value,
            assessment_snapshot_id=report_input.request_hash or dedup_hash,
            generation_version=self.REPORT_VERSION,
            retry_count=0,
        )
        
        self.db.add(job)
        self.db.commit()
        logger.info(f"Created report job {job_id} for user {user_id}")
        return job_id
    
    def get_status(self, job_id: str) -> Optional[ReportJobStatus]:
        """Get current status of report job."""
        job = self.db.query(ReportJob).filter(ReportJob.id == job_id).first()
        if not job:
            return None
        
        return self._job_to_status(job)
    
    def start_generation(self, job_id: str) -> bool:
        """Mark job as running."""
        job = self.db.query(ReportJob).filter(ReportJob.id == job_id).first()
        if not job:
            return False
        
        job.status = ReportStatus.RUNNING.value
        job.started_at = datetime.utcnow()
        self.db.commit()
        return True
    
    def mark_completed(
        self, 
        job_id: str,
        artifact_path: str,
        artifact_size: int
    ) -> bool:
        """Mark job as completed with artifact metadata."""
        job = self.db.query(ReportJob).filter(ReportJob.id == job_id).first()
        if not job:
            return False
        
        job.status = ReportStatus.COMPLETED.value
        job.completed_at = datetime.utcnow()
        job.artifact_path = artifact_path
        job.artifact_size = artifact_size
        job.artifact_created_at = datetime.utcnow()
        self.db.commit()
        logger.info(f"Job {job_id} completed: {artifact_path}")
        return True
    
    def mark_failed(
        self,
        job_id: str,
        error_message: str,
        error_details: Optional[str] = None,
        should_retry: bool = True
    ) -> bool:
        """Mark job as failed and optionally schedule retry."""
        job = self.db.query(ReportJob).filter(ReportJob.id == job_id).first()
        if not job:
            return False
        
        job.error_message = error_message
        job.error_details = error_details
        
        if should_retry and job.retry_count < job.max_retries:
            job.status = ReportStatus.RETRYING.value
            job.retry_count += 1
            # Exponential backoff: 5min, 15min, 45min
            backoff_seconds = (5 * 60) * (3 ** (job.retry_count - 1))
            job.next_retry_at = datetime.utcnow() + timedelta(seconds=backoff_seconds)
            logger.info(f"Job {job_id} scheduled for retry #{job.retry_count}")
        else:
            job.status = ReportStatus.FAILED.value
            logger.error(f"Job {job_id} failed permanently: {error_message}")
        
        self.db.commit()
        return True
    
    def get_pending_jobs(self, limit: int = 10) -> list[str]:
        """Get list of pending job IDs."""
        jobs = self.db.query(ReportJob).filter(
            ReportJob.status == ReportStatus.PENDING.value
        ).limit(limit).all()
        return [job.id for job in jobs]
    
    def get_retryable_jobs(self) -> list[str]:
        """Get jobs that are due for retry."""
        now = datetime.utcnow()
        jobs = self.db.query(ReportJob).filter(
            ReportJob.status == ReportStatus.RETRYING.value,
            ReportJob.next_retry_at <= now
        ).all()
        return [job.id for job in jobs]
    
    @staticmethod
    def _compute_input_hash(
        user_id: int,
        report_type: ReportType,
        report_input: ReportInput
    ) -> str:
        """Generate deterministic hash of report inputs."""
        key = f"{user_id}:{report_type.value}:{json.dumps(report_input.__dict__, sort_keys=True)}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]
    
    @staticmethod
    def _job_to_status(job: ReportJob) -> ReportJobStatus:
        """Convert database job to status DTO."""
        artifact = None
        if job.artifact_path:
            artifact = ReportArtifact(
                path=job.artifact_path,
                size_bytes=job.artifact_size or 0,
                created_at=job.artifact_created_at or datetime.utcnow()
            )
        
        return ReportJobStatus(
            job_id=job.id,
            user_id=job.user_id,
            status=ReportStatus(job.status),
            report_type=ReportType(job.report_type),
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            artifact=artifact,
            error=job.error_message,
            retry_count=job.retry_count,
            max_retries=job.max_retries,
            next_retry_at=job.next_retry_at,
        )