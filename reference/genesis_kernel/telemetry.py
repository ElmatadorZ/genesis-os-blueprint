"""
genesis_kernel.telemetry — the kernel's ninth service: Explain records + audit spine.

Kernel guarantee K3: for every event, decision, and outcome, a record MUST be emitted. Absence
of a record is itself a detectable fault. Records are append-only.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Record:
    kind: str          # "event" | "decision" | "routing" | "outcome"
    data: Dict[str, Any]
    ts: float = field(default_factory=time.time)


class Telemetry:
    def __init__(self) -> None:
        self._records: List[Record] = []

    def emit(self, kind: str, **data: Any) -> None:
        self._records.append(Record(kind=kind, data=dict(data)))

    def records(self, kind: Optional[str] = None) -> List[Record]:
        return [r for r in self._records if kind is None or r.kind == kind]

    def count(self, kind: Optional[str] = None) -> int:
        return len(self.records(kind))

    def explain(self) -> str:
        """A human-readable rendering of the whole audit trail — the 'why' of the run."""
        lines: List[str] = []
        for r in self._records:
            if r.kind == "decision":
                verdict = "ALLOW" if r.data.get("allow") else "DENY "
                lines.append(f"  · [{r.data.get('point'):<12}] {verdict} {r.data.get('policy'):<20} "
                             f"— {r.data.get('reason')}")
            elif r.kind == "routing":
                ok = "ok" if r.data.get("ok") else "skip/none"
                lines.append(f"  · route {r.data.get('capability')} -> {r.data.get('provider')} ({ok})")
            elif r.kind == "outcome":
                lines.append(f"  = OUTCOME: {r.data.get('status')} — {r.data.get('detail','')}")
            elif r.kind == "event":
                lines.append(f"  → event {r.data.get('type')} [{r.data.get('id')}]")
        return "\n".join(lines)
