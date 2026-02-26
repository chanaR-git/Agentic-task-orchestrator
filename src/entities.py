from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskType(Enum):
    UNKNOWN = "unknown"
    BUG = "bug"
    FEATURE = "feature"
    IMPROVEMENT = "improvement"


@dataclass
class Task:
    """Represents a task in the system."""

    code: str
    title: str
    description: Optional[str] = None
    type: TaskType = TaskType.UNKNOWN
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: TaskStatus = TaskStatus.PENDING
