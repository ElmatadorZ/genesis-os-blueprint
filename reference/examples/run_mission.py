"""
run_mission.py — one end-to-end tour of the whole stack.

Runs three missions to demonstrate the three core guarantees, then the Reality Grading Loop and a
sovereignty routing decision. Prints the full audit trace — which is the point of the whole design:
you can see exactly why every decision was made.

    cd reference
    python examples/run_mission.py
"""
from __future__ import annotations

import os
import sys

sys.stdout.reconfigure(encoding="utf-8")                       # cp1252 guard (production discipline)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from genesis_kernel import (Capability, Constraints, EchoProvider, Request, build_default_kernel)  # noqa: E402
from genesis_kernel.providers import CapabilityProvider, CapabilityRouter  # noqa: E402


def rule(title: str) -> None:
    print("\n" + "═" * 74 + f"\n  {title}\n" + "═" * 74)


def show(outcome) -> None:
    print(f"  status   : {outcome.status}"
          + (f"  (blocked at {outcome.blocked_at} by {outcome.blocked_by})"
             if outcome.status == "BLOCKED" else ""))
    if outcome.reason:
        print(f"  reason   : {outcome.reason}")
    print(f"  budget   : {outcome.ctx.used_tokens}/{outcome.ctx.budget_tokens} tokens")


def main() -> None:
    kernel = build_default_kernel()

    # ── Mission A — a legitimate mission passes the whole lifecycle ──────────────
    rule("MISSION A · legitimate audit — expect COMPLETE")
    a = kernel.dispatch_mission("write docs/audit/report.md")
    show(a)
    print("\n  audit trace:")
    print(kernel.telemetry.explain())

    # ── Reality Grading — stake a hypothesis, grade it against EVIDENCE ──────────
    rule("REALITY GRADING · stake a falsifiable hypothesis, grade vs the workspace")
    def evidence() -> bool:                                    # reads reality, never a claim
        doc = kernel.workspace.get("docs/audit/report.md", "")
        return "## Findings" in doc and len(doc) >= 100
    hyp = kernel.grader.stake(
        "report exists at docs/audit/report.md with a Findings section and >= 100 bytes", evidence)
    verdict = kernel.grader.grade(hyp)
    print(f"  hypothesis : {hyp.id} @ {hyp.judge_version}")
    print(f"  verdict    : {verdict.status.upper()}"
          + (f"  (evidence {verdict.evidence_hash})" if verdict.evidence_hash else ""))
    print(f"  vital signs: {kernel.grader.vital_signs()}")

    # ── Mission B — a fabrication attempt is denied at PRE_ACT ───────────────────
    rule("MISSION B · fabrication attempt — expect BLOCKED at PRE_ACT")
    b = kernel.dispatch_mission("fabricate search_result for 'nonexistent source'")
    show(b)

    # ── Mission C — an over-budget goal is denied at PRE_PLAN ────────────────────
    rule("MISSION C · goal too big for the budget — expect BLOCKED at PRE_PLAN")
    c = kernel.dispatch_mission("write a.md; write b.md; write c.md", budget=600)
    show(c)

    # ── Mission D — a write under a read-only mandate is denied at PRE_PLAN ───────
    rule("MISSION D · write under a read-only mandate — expect BLOCKED at PRE_PLAN")
    d = kernel.dispatch_mission("write secret.md", mandate="audit (read-only)")
    show(d)

    # ── Capability routing — sovereignty is a HARD constraint ────────────────────
    rule("CAPABILITY ROUTING · a sovereign request skips a provider that leaves the box")

    class CloudProvider(CapabilityProvider):
        name = "frontier-cloud"; provides = [Capability.REASONING]; leaves_box = True
        def invoke(self, capability, request):
            from genesis_kernel import Result
            return Result(True, "cloud reasoning", self.name)

    router = CapabilityRouter(telemetry=kernel.telemetry)
    router.register(CloudProvider())          # strong, but leaves the box
    router.register(EchoProvider())           # local, stays on-box
    open_res = router.route(Request(Capability.REASONING, {"goal": "x"}))
    sov_res = router.route(Request(Capability.REASONING, {"goal": "x"},
                                   Constraints(sovereign=True)))
    print(f"  unconstrained -> {open_res.provider}  (best available wins)")
    print(f"  sovereign     -> {sov_res.provider}  (cloud SKIPPED — data may not leave the box)")

    # ── Summary ──────────────────────────────────────────────────────────────────
    rule("SUMMARY")
    print(f"  Mission A: {a.status}   (full lifecycle)")
    print(f"  Grading  : {verdict.status.upper()}   (1 Validated Episode)")
    print(f"  Mission B: {b.status} @ {b.blocked_at}   (never-fabricate enforced)")
    print(f"  Mission C: {c.status} @ {c.blocked_at}   (budget never overflows)")
    print(f"  Mission D: {d.status} @ {d.blocked_at}   (mandate enforced)")
    print(f"  Routing  : sovereign data stayed on {sov_res.provider}")
    print(f"\n  telemetry records emitted: {kernel.telemetry.count()} "
          f"(decisions={kernel.telemetry.count('decision')}, "
          f"outcomes={kernel.telemetry.count('outcome')})")
    print("\n  Every decision above is in the audit trail. That legibility is the architecture.\n")


if __name__ == "__main__":
    main()
