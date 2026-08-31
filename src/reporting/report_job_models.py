"""Type definitions and data classes for report jobs."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import json


class ReportStatus(str, Enum):
    """Report job status lifecycle."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class ReportType(str, Enum):
    """Types of reports that can be generated."""
    MONTHLY = "monthly"
    ANNUAL = "annual"
    CUSTOM = "custom"
    ASSESSMENT = "assessment"


@dataclass
class ReportInput:
    """Reproducible inputs for report generation."""
    user_id: int
    report_type: ReportType
    
    # Data snapshots - these versions are captured at request time
    assessment_data: dict = field(default_factory=dict)
    metrics_data: dict = field(default_factory=dict)
    goals_data: dict = field(default_factory=dict)
    recommendations_data: dict = field(default_factory=dict)
    
    # Optional parameters
    custom_title: Optional[str] = None
    include_charts: bool = True
    include_recommendations: bool = True
    
    # Deduplication key
    request_hash: Optional[str] = None


@dataclass
class ReportArtifact:
    """Metadata about generated report file."""
    path: str
    size_bytes: int
    created_at: datetime
    format: str = "pdf"  # pdf, xlsx, etc.
    checksum: Optional[str] = None


@dataclass
class ReportJobStatus:
    """Current status of a report generation job."""
    job_id: str
    user_id: int
    status: ReportStatus
    report_type: ReportType
    
    # Progress tracking
    progress_percent: int = 0
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Result info
    artifact: Optional[ReportArtifact] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    next_retry_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = {
            "job_id": self.job_id,
            "user_id": self.user_id,
            "status": self.status.value,
            "report_type": self.report_type.value,
            "progress_percent": self.progress_percent,
            "created_at": self.created_at.isoformat(),
            "error": self.error,
            "retry_count": self.retry_count,
        }
        if self.started_at:
            result["started_at"] = self.started_at.isoformat()
        if self.completed_at:
            result["completed_at"] = self.completed_at.isoformat()
        if self.artifact:
            result["artifact"] = {
                "path": self.artifact.path,
                "size_bytes": self.artifact.size_bytes,
                "created_at": self.artifact.created_at.isoformat(),
                "format": self.artifact.format,
            }
        if self.next_retry_at:
            result["next_retry_at"] = self.next_retry_at.isoformat()
        return result