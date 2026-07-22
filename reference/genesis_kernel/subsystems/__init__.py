"""Cognitive Subsystems — single-responsibility plugins that conform to the Kernel ABI."""
from .execution import ExecutionSubsystem
from .governance import GovernanceSubsystem
from .memory import MemorySubsystem
from .planning import PlanningSubsystem
from .validation import ValidationSubsystem

__all__ = [
    "PlanningSubsystem", "ExecutionSubsystem", "ValidationSubsystem",
    "MemorySubsystem", "GovernanceSubsystem",
]
