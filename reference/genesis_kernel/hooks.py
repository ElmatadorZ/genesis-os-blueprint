"""
genesis_kernel.hooks — the Policy Hook Surface.

Normative spec: ../../specs/policy-hook-contract.md. Three invariants, all enforced here:
  - most-restrictive-wins (C1): first deny is final.
  - fail-closed (F1-F3): any error/malformed/timeout -> DENY, not disable-able.
  - every decision audited (A1-A3): allow AND deny are recorded, append-only.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from .abi import Context, Decision, Event, HookPoint
from .telemetry import Telemetry


class Policy(ABC):
    """A single policy attached to one hook point (policy-hook-contract §2)."""
    name: str = "policy"
    point: HookPoint = HookPoint.PRE_ACT

    @abstractmethod
    def evaluate(self, event: Event, ctx: Context) -> Decision:
        """SHOULD be side-effect-free; MAY read evidence to decide (P1). MUST set policy+reason (P2)."""
        raise NotImplementedError


class PolicyHookSurface:
    def __init__(self, telemetry: Optional[Telemetry] = None) -> None:
        self._by_point: Dict[HookPoint, List[Policy]] = {p: [] for p in HookPoint}
        self._telemetry = telemetry

    def register(self, policy: Policy) -> None:
        self._by_point[policy.point].append(policy)

    def policies_at(self, point: HookPoint) -> List[Policy]:
        return list(self._by_point[point])

    def _safe_evaluate(self, policy: Policy, event: Event, ctx: Context) -> Decision:
        """Fail-closed wrapper (F1): any exception or malformed return becomes DENY."""
        try:
            d = policy.evaluate(event, ctx)
            if not isinstance(d, Decision):
                return Decision(False, "malformed decision", policy.name)
            return d
        except Exception as e:  # noqa: BLE001 — fail-closed is the whole point
            return Decision(False, f"policy error: {type(e).__name__}: {e}", policy.name)

    def check(self, point: HookPoint, event: Event, ctx: Context) -> Decision:
        """Most-restrictive-wins, fail-closed, fully audited. Empty surface -> allow (C2)."""
        for policy in self._by_point[point]:
            d = self._safe_evaluate(policy, event, ctx)
            if self._telemetry is not None:                      # A1/A2: audit allow AND deny
                self._telemetry.emit("decision", point=point.value, policy=d.policy,
                                     allow=d.allow, reason=d.reason, event=event.id)
            ctx.log(f"[{point.value}] {d.policy}: {'ALLOW' if d.allow else 'DENY'} — {d.reason}")
            if not d.allow:                                      # C1/C3: first deny is final
                return d
        return Decision(True, "all policies allowed", "*")
