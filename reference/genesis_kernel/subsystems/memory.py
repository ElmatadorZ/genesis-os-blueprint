"""Memory subsystem — recall/persist over the canonical store (Capability.MEMORY).

State Ownership Principle (docs §06): this is the ONE canonical store. Everything else is a
read-only projection. A real implementation would be the provenance graph; here it is a dict.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from ..abi import Capability, Context, Event, Subsystem


class MemorySubsystem(Subsystem):
    name = "memory"
    provides = [Capability.MEMORY]

    def __init__(self) -> None:
        self._store: Dict[str, Any] = {}   # the single source of truth

    def handle(self, event: Event, ctx: Context) -> Optional[Event]:
        # Not on the mission critical path in the demo; recall/persist are called directly.
        return None

    def persist(self, key: str, value: Any) -> None:
        self._store[key] = value

    def recall(self, key: str) -> Any:
        return self._store.get(key)

    def size(self) -> int:
        return len(self._store)
