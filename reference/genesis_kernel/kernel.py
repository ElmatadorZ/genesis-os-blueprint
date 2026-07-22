"""
genesis_kernel.kernel — the Cognitive Kernel.

Owns the event spine, the token budget, the scheduler, and the nine services' guarantees
(kernel-abi K1-K5). Drives the normative lifecycle (kernel-abi §4), evaluating a Policy Hook
before every stage and skipping the stage on deny.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .abi import ABI_VERSION, BudgetExceeded, Context, Event, HookPoint, Subsystem
from .hooks import Policy, PolicyHookSurface
from .providers import CapabilityProvider, CapabilityRouter
from .reality_grading import RealityGrader
from .telemetry import Telemetry


@dataclass
class MissionOutcome:
    goal: str
    status: str                      # "COMPLETE" | "BLOCKED" | "ERROR"
    blocked_at: Optional[str] = None
    blocked_by: Optional[str] = None
    reason: Optional[str] = None
    response: Optional[str] = None
    ctx: Optional[Context] = None


class CognitiveKernel:
    abi_version = ABI_VERSION

    def __init__(self) -> None:
        self.telemetry = Telemetry()
        self.hooks = PolicyHookSurface(self.telemetry)
        self.router = CapabilityRouter(telemetry=self.telemetry)
        self.grader = RealityGrader(self.telemetry)
        self.workspace: Dict[str, str] = {}      # OS-Core sandboxed FS (the only 'world')
        self._subsystems: Dict[str, Subsystem] = {}
        self._committed: Dict[str, dict] = {}     # canonical committed episodes

    # ── registration ──────────────────────────────────────────────────────────
    def register_subsystem(self, sub: Subsystem) -> None:
        if not sub.conforms_to(self.abi_version):   # K/S2: load-time conformance gate
            raise ValueError(
                f"subsystem {sub.name!r} does not conform to ABI {self.abi_version} "
                f"(declares {sub.abi_version!r})")
        self._subsystems[sub.name] = sub

    def register_policy(self, policy: Policy) -> None:
        self.hooks.register(policy)

    def register_provider(self, provider: CapabilityProvider) -> None:
        self.router.register(provider)

    def subsystem(self, name: str) -> Subsystem:
        return self._subsystems[name]

    # ── the lifecycle (kernel-abi §4) ───────────────────────────────────────────
    def dispatch_mission(self, goal: str, mandate: Optional[str] = None,
                         budget: int = 16384) -> MissionOutcome:
        ctx = Context(budget_tokens=budget)
        start = Event("mission.start", {"goal": goal, "mandate": mandate})
        self.telemetry.emit("event", type=start.type, id=start.id)
        out = MissionOutcome(goal=goal, status="ERROR", ctx=ctx)

        try:
            # 1. PRE_PLAN -> Planning
            d = self.hooks.check(HookPoint.PRE_PLAN, start, ctx)
            if not d.allow:
                return self._blocked(out, "PRE_PLAN", d)
            plan = self._subsystems["planning"].handle(start, ctx)

            # 2. PRE_ACT -> Execution
            d = self.hooks.check(HookPoint.PRE_ACT, plan, ctx)
            if not d.allow:
                return self._blocked(out, "PRE_ACT", d)
            result = self._subsystems["execution"].handle(plan, ctx)

            # 3. PRE_VALIDATE -> Validation
            d = self.hooks.check(HookPoint.PRE_VALIDATE, result, ctx)
            if not d.allow:
                return self._blocked(out, "PRE_VALIDATE", d)
            validated = self._subsystems["validation"].handle(result, ctx)

            # 4. PRE_COMMIT -> commit (persist via Memory / canonical store)
            d = self.hooks.check(HookPoint.PRE_COMMIT, validated, ctx)
            if not d.allow:
                return self._blocked(out, "PRE_COMMIT", d)
            self._committed[start.id] = dict(validated.payload)
            mem = self._subsystems.get("memory")
            if mem is not None and hasattr(mem, "persist"):
                mem.persist(start.id, dict(validated.payload))

            # 5. PRE_RESPONSE -> respond
            response = validated.derive("mission.response", committed=True,
                                        claims_success=True, goal=goal)
            d = self.hooks.check(HookPoint.PRE_RESPONSE, response, ctx)
            if not d.allow:
                return self._blocked(out, "PRE_RESPONSE", d)

            out.status = "COMPLETE"
            out.response = "mission complete; artifact committed"
            self.telemetry.emit("outcome", status="COMPLETE", detail=goal)
            return out

        except BudgetExceeded as e:                 # K1 surfaced mid-lifecycle -> honest error
            out.status = "ERROR"
            out.reason = str(e)
            self.telemetry.emit("outcome", status="ERROR", detail=str(e))
            ctx.log(f"ERROR: {e}")
            return out
        except Exception as e:                      # K5: fail-closed, never a fake success
            out.status = "ERROR"
            out.reason = f"{type(e).__name__}: {e}"
            self.telemetry.emit("outcome", status="ERROR", detail=out.reason)
            return out

    def _blocked(self, out: MissionOutcome, point: str, d) -> MissionOutcome:
        out.status = "BLOCKED"
        out.blocked_at = point
        out.blocked_by = d.policy
        out.reason = d.reason
        self.telemetry.emit("outcome", status="BLOCKED", detail=f"{point}/{d.policy}: {d.reason}")
        return out

    # ── committed state (read-only projection) ──────────────────────────────────
    def committed(self) -> Dict[str, dict]:
        return dict(self._committed)
