"""Execution subsystem — carry out plan steps (Capability.EXECUTION).

S3: a subsystem MUST NOT touch the outside world directly. Here the only 'world' is the kernel's
sandboxed workspace (a dict standing in for the OS Core's sandboxed FS). A real implementation
would request the effect from the kernel, which would perform it via an audited OS-Core syscall.
"""
from __future__ import annotations

from typing import Dict, Optional

from ..abi import Capability, Context, Event, Subsystem

_REPORT_BODY = (
    "# Audit Report\n\n"
    "## Findings\n"
    "- The system dispatched the mission through the full kernel lifecycle.\n"
    "- Every step crossed the Policy Hook Surface and was audited.\n"
    "- This artifact is the evidence a hypothesis will be graded against.\n"
)


class ExecutionSubsystem(Subsystem):
    name = "execution"
    provides = [Capability.EXECUTION]

    def __init__(self, workspace: Dict[str, str]) -> None:
        self.workspace = workspace  # the sandboxed FS the kernel owns

    def handle(self, event: Event, ctx: Context) -> Optional[Event]:
        results = []
        for step in event.payload.get("steps", []) or []:
            ctx.spend(500)  # S4: each step costs budget
            results.append(self._do(str(step)))
        ctx.log(f"execution: performed {len(results)} step(s)")
        return event.derive("mission.result", results=results, goal=event.payload.get("goal"))

    def _do(self, step: str) -> Dict[str, str]:
        low = step.strip().lower()
        if low.startswith("write "):
            path = step.strip()[6:].strip()
            self.workspace[path] = _REPORT_BODY
            return {"step": step, "effect": f"wrote {path} ({len(_REPORT_BODY)} bytes)"}
        # non-mutating step: compute/read
        return {"step": step, "effect": "computed (no outside effect)"}
