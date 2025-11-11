from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class ErrorContext:
    """Context information for an error occurrence"""
    code: int
    timestamp: float
    state: Optional[str] = None
    operation: Optional[str] = None
    additional_data: Dict[str, Any] = None
    stack_trace: Optional[str] = None
    recovery_attempted: bool = False
    recovery_successful: bool = False

    def __post_init__(self):
        if self.additional_data is None:
            self.additional_data = {}