"""Validation subsystem — the cognitive quality gate (Capability.VALIDATION)."""
from __future__ import annotations

from typing import Optional

from ..abi import Capability, Context, Event, Subsystem


class ValidationSubsystem(Subsystem):
    name = "validation"
    provides = [Capability.VALIDATION]

    def handle(self, event: Event, ctx: Context) -> Optional[Event]:
        ctx.spend(150)
        results = event.payload.get("results", []) or []
        # A real gate would check correctness/quality; here: every step must have produced an effect.
        ok = bool(results) and all(r.get("effect") for r in results)
        ctx.log(f"validation: {'PASS' if ok else 'FAIL'} over {len(results)} result(s)")
        return event.derive("mission.validated", validated=ok, results=results,
                            goal=event.payload.get("goal"))
