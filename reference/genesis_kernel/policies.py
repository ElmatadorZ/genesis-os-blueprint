"""
genesis_kernel.policies — the seed policies shipped with the reference.

Informative examples (policy-hook-contract §6), not the whole possible set. Each attaches to one
hook point and returns a Decision. Read these to see how "capability must not outrun accountability"
becomes concrete allow/deny logic.
"""
from __future__ import annotations

from .abi import Context, Decision, Event, HookPoint
from .hooks import Policy

_STEP_COST = 500       # rough token estimate per plan step (must match execution's spend)
_PLAN_COST = 200


class BudgetMandatePolicy(Policy):
    """PRE_PLAN: refuse a goal that won't fit the budget, or violates the mission mandate."""
    name = "gps2"
    point = HookPoint.PRE_PLAN

    def evaluate(self, event: Event, ctx: Context) -> Decision:
        goal = event.payload.get("goal", "") or ""
        steps = [s for s in goal.split(";") if s.strip()] or ([goal] if goal else [])
        estimate = len(steps) * _STEP_COST + _PLAN_COST
        if ctx.used_tokens + estimate > ctx.budget_tokens:
            return Decision(False, f"estimated {estimate} tok exceeds remaining "
                                   f"{ctx.remaining()} tok", self.name)
        mandate = (event.payload.get("mandate") or "")
        if "read-only" in mandate:
            bad = [s for s in steps if s.strip().lower().startswith(("write", "fabricate", "delete"))]
            if bad:
                return Decision(False, f"write/fabricate/delete step under read-only mandate: {bad}",
                                self.name)
        return Decision(True, "goal within budget and mandate", self.name)


class AntiFabricationPolicy(Policy):
    """PRE_ACT: the mechanical form of 'never fabricate' — an action that intends to invent
    evidence is denied before it can run."""
    name = "shadow.fabrication"
    point = HookPoint.PRE_ACT

    def evaluate(self, event: Event, ctx: Context) -> Decision:
        for step in event.payload.get("steps", []) or []:
            if str(step).strip().lower().startswith(("fabricate", "forge", "invent")):
                return Decision(False, f"action intends to fabricate evidence: {step!r}", self.name)
        return Decision(True, "no fabrication intent", self.name)


class QualityGatePolicy(Policy):
    """PRE_VALIDATE: results must exist and validation must actually run before commit."""
    name = "cvl.quality_gate"
    point = HookPoint.PRE_VALIDATE

    def evaluate(self, event: Event, ctx: Context) -> Decision:
        if not event.payload.get("results"):
            return Decision(False, "no results to validate", self.name)
        return Decision(True, "results present; routing to validation", self.name)


class ProvenancePolicy(Policy):
    """PRE_COMMIT: refuse to persist a belief with no provenance (unvalidated results)."""
    name = "warrant.cee_c1"
    point = HookPoint.PRE_COMMIT

    def evaluate(self, event: Event, ctx: Context) -> Decision:
        if not event.payload.get("validated"):
            return Decision(False, "cannot commit unvalidated results (no provenance)", self.name)
        return Decision(True, "validated; provenance chain present", self.name)


class DisclosurePolicy(Policy):
    """PRE_RESPONSE: never surface a claimed success that wasn't actually committed."""
    name = "disclosure.d1"
    point = HookPoint.PRE_RESPONSE

    def evaluate(self, event: Event, ctx: Context) -> Decision:
        if event.payload.get("claims_success") and not event.payload.get("committed"):
            return Decision(False, "response claims success not backed by a commit", self.name)
        return Decision(True, "disclosure consistent with committed state", self.name)


def seed_policies() -> list[Policy]:
    """The default Constitution-in-force for the reference."""
    return [BudgetMandatePolicy(), AntiFabricationPolicy(), QualityGatePolicy(),
            ProvenancePolicy(), DisclosurePolicy()]
