"""
test_kernel.py — deterministic, offline conformance checks for the reference.

Proves the invariants the specs require. No network, no keys, no clocks that matter. Runs under
pytest, or standalone:  python tests/test_kernel.py
"""
from __future__ import annotations

import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from genesis_kernel import (ABI_VERSION, BudgetExceeded, Capability, CognitiveKernel, Constraints,  # noqa: E402
                            Context, Decision, EchoProvider, Event, HookPoint, Request,
                            build_default_kernel)
from genesis_kernel.hooks import Policy, PolicyHookSurface  # noqa: E402
from genesis_kernel.providers import CapabilityProvider, CapabilityRouter, Result  # noqa: E402
from genesis_kernel.subsystems import PlanningSubsystem  # noqa: E402


# ── ABI: budget never overflows (K1) ────────────────────────────────────────────
def test_budget_never_overflows():
    ctx = Context(budget_tokens=100)
    ctx.spend(60)
    assert ctx.used_tokens == 60
    try:
        ctx.spend(50)
    except BudgetExceeded as e:
        assert e.requested == 50 and e.used == 60
    else:
        assert False, "expected BudgetExceeded"
    assert ctx.used_tokens == 60          # over-spend MUST NOT mutate used_tokens


# ── ABI: load-time conformance gate (S2) ─────────────────────────────────────────
def test_nonconforming_subsystem_refused():
    k = CognitiveKernel()
    bad = PlanningSubsystem()
    bad.abi_version = "9.9"                # deliberately wrong
    try:
        k.register_subsystem(bad)
    except ValueError:
        pass
    else:
        assert False, "kernel must refuse a non-conforming subsystem"


# ── Hooks: most-restrictive-wins (C1) ────────────────────────────────────────────
def test_most_restrictive_wins():
    class Allow(Policy):
        name = "allow"; point = HookPoint.PRE_ACT
        def evaluate(self, e, c): return Decision(True, "ok", self.name)
    class Deny(Policy):
        name = "deny"; point = HookPoint.PRE_ACT
        def evaluate(self, e, c): return Decision(False, "nope", self.name)
    s = PolicyHookSurface()
    s.register(Allow()); s.register(Deny())
    d = s.check(HookPoint.PRE_ACT, Event("x"), Context())
    assert d.allow is False and d.policy == "deny"


# ── Hooks: fail-closed (F1) — a throwing policy denies ───────────────────────────
def test_fail_closed_on_policy_error():
    class Boom(Policy):
        name = "boom"; point = HookPoint.PRE_ACT
        def evaluate(self, e, c): raise RuntimeError("kaboom")
    s = PolicyHookSurface()
    s.register(Boom())
    d = s.check(HookPoint.PRE_ACT, Event("x"), Context())
    assert d.allow is False and "policy error" in d.reason


# ── Hooks: empty surface allows (C2) ─────────────────────────────────────────────
def test_empty_hook_allows():
    d = PolicyHookSurface().check(HookPoint.PRE_PLAN, Event("x"), Context())
    assert d.allow is True


# ── Providers: sovereignty is a hard constraint (IN1) ────────────────────────────
def test_sovereign_request_skips_offbox_provider():
    class Cloud(CapabilityProvider):
        name = "cloud"; provides = [Capability.REASONING]; leaves_box = True
        def invoke(self, cap, req): return Result(True, "cloud", self.name)
    r = CapabilityRouter()
    r.register(Cloud()); r.register(EchoProvider())
    assert r.route(Request(Capability.REASONING, {"goal": "x"})).provider == "cloud"
    sov = r.route(Request(Capability.REASONING, {"goal": "x"}, Constraints(sovereign=True)))
    assert sov.provider == "echo-local"     # cloud skipped, not errored


# ── Providers: unavailable is skipped, not errored (AV1); no fabrication (RT3) ────
def test_unavailable_skipped_and_no_fabrication():
    class Off(CapabilityProvider):
        name = "off"; provides = [Capability.MEMORY]
        def available(self): return False
        def invoke(self, cap, req): return Result(True, "should never run", self.name)
    r = CapabilityRouter()
    r.register(Off())
    res = r.route(Request(Capability.MEMORY))
    assert res.ok is False and res.provider == "*"    # explicit failure, not a fabricated result


# ── Lifecycle: a legitimate mission COMPLETES ────────────────────────────────────
def test_mission_complete():
    k = build_default_kernel()
    out = k.dispatch_mission("write docs/audit/report.md")
    assert out.status == "COMPLETE"
    assert "docs/audit/report.md" in k.workspace
    assert len(k.committed()) == 1


# ── Lifecycle: fabrication blocked at PRE_ACT ────────────────────────────────────
def test_fabrication_blocked():
    k = build_default_kernel()
    out = k.dispatch_mission("fabricate a result")
    assert out.status == "BLOCKED" and out.blocked_at == "PRE_ACT"
    assert out.blocked_by == "shadow.fabrication"


# ── Lifecycle: over-budget blocked at PRE_PLAN ───────────────────────────────────
def test_over_budget_blocked():
    k = build_default_kernel()
    out = k.dispatch_mission("write a.md; write b.md; write c.md", budget=600)
    assert out.status == "BLOCKED" and out.blocked_at == "PRE_PLAN"


# ── Lifecycle: read-only mandate blocks a write at PRE_PLAN ───────────────────────
def test_read_only_mandate_blocks_write():
    k = build_default_kernel()
    out = k.dispatch_mission("write secret.md", mandate="audit (read-only)")
    assert out.status == "BLOCKED" and out.blocked_at == "PRE_PLAN"


# ── Reality Grading: evidence-based confirm + fail-closed refute ──────────────────
def test_reality_grading_confirm_and_refute():
    k = build_default_kernel()
    k.dispatch_mission("write docs/audit/report.md")
    good = k.grader.stake("report present",
                          lambda: "docs/audit/report.md" in k.workspace)
    assert k.grader.grade(good).status == "confirmed"
    assert len(k.grader.validated_episodes()) == 1

    bad = k.grader.stake("nonexistent file present",
                         lambda: "nope.md" in k.workspace)
    assert k.grader.grade(bad).status == "refuted"

    err = k.grader.stake("query errors", lambda: (_ for _ in ()).throw(ValueError()))
    assert k.grader.grade(err).status == "refuted"    # fail-closed: unverifiable != success

    assert k.grader.grade(good, evidence_available=False).status == "abstain"


# ── Telemetry: every dispatched mission emits records (K3) ────────────────────────
def test_telemetry_records_everything():
    k = build_default_kernel()
    k.dispatch_mission("write docs/audit/report.md")
    assert k.telemetry.count("decision") >= 5     # one per hook on the happy path
    assert k.telemetry.count("outcome") >= 1


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        fn(); passed += 1
        print(f"  ok  {fn.__name__}")
    print(f"\n{passed}/{len(fns)} passed")
