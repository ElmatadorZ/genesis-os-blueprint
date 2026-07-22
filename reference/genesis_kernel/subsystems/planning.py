"""Planning subsystem — decompose a goal into ordered steps (Capability.PLANNING)."""
from __future__ import annotations

from typing import Optional

from ..abi import Capability, Context, Event, Subsystem
from ..providers import CapabilityRouter, Constraints, Request


class PlanningSubsystem(Subsystem):
    name = "planning"
    provides = [Capability.PLANNING]

    def __init__(self, router: Optional[CapabilityRouter] = None) -> None:
        self.router = router

    def handle(self, event: Event, ctx: Context) -> Optional[Event]:
        ctx.spend(200)  # S4: planning costs budget, accounted before use
        goal = event.payload.get("goal", "") or ""
        mandate = event.payload.get("mandate")

        # Ask a provider for the decomposition (REASONING/PLANNING) — model-independent (docs §04).
        steps = None
        if self.router is not None:
            res = self.router.route(Request(Capability.PLANNING, {"goal": goal},
                                            Constraints(deterministic=True)))
            if res.ok:
                steps = res.output
        if not steps:
            steps = [s.strip() for s in goal.split(";") if s.strip()] or ([goal] if goal else [])

        ctx.log(f"planning: decomposed goal into {len(steps)} step(s)")
        return event.derive("mission.act", steps=steps, goal=goal, mandate=mandate)
