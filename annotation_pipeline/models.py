"""Data models for annotation pipeline."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Item:
    id: str
    raw_data: str
    stage: str
    annotator_id: Optional[str]
    priority: str
    created_at: datetime
    stage_entered_at: datetime
    rejection_note: Optional[str]


@dataclass
class Annotator:
    id: str
    items_completed: int
    items_rejected: int
    avg_cycle_time_hrs: float


@dataclass
class Event:
    id: int
    item_id: str
    event_type: str
    from_stage: Optional[str]
    to_stage: Optional[str]
    timestamp: datetime


VALID_STAGES = ["UPLOAD", "ANNOTATE", "REVIEW", "APPROVED", "REJECTED"]
VALID_PRIORITIES = ["high", "medium", "low"]
