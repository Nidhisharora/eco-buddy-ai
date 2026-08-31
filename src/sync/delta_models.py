import dataclasses
from typing import Optional

@dataclasses.dataclass
class EcoLogDelta:
    """
    Data model representing a synchronization delta.
    Contains the crucial metadata required for timestamp-based conflict resolution (Issue #1473).
    """
    id: str
    user_id: str
    activity_type: str
    points: int
    last_modified: int # Unix timestamp in milliseconds for precision conflict resolution
    is_deleted: bool   # Tombstone flag for soft-deletes
    
    def to_dict(self):
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)
