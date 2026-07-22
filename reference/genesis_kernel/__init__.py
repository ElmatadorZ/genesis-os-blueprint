"""
Genesis OS — Cognitive Agent Architecture Blueprint · reference implementation.

Dependency-free (standard library only). See ../../docs for the architecture and ../../specs for
the normative contracts this package is the runnable oracle for.

Quick start:
    from genesis_kernel import build_default_kernel
    kernel = build_default_kernel()
    outcome = kernel.dispatch_mission("write docs/audit/report.md")
"""
from __future__ import annotations

from .abi import (ABI_VERSION, BudgetExceeded, Capability, Context, Decision, Event, HookPoint,
                  Subsystem)
from .hooks import Policy, PolicyHookSurface
from .kernel import CognitiveKernel, MissionOutcome
from .policies import seed_policies
from .providers import (CapabilityProvider, CapabilityRouter, Constraints, EchoProvider, Request,
                        Result)
from .reality_grading import Hypothesis, JUDGE_VERSION, RealityGrader, Verdict
from .subsystems import (ExecutionSubsystem, GovernanceSubsystem, MemorySubsystem,
                         PlanningSubsystem, ValidationSubsystem)
from .telemetry import Telemetry

__version__ = "0.2.0"

__all__ = [
    "ABI_VERSION", "Capability", "HookPoint", "Event", "Context", "Decision", "Subsystem",
    "BudgetExceeded", "Policy", "PolicyHookSurface", "CognitiveKernel", "MissionOutcome",
    "CapabilityProvider", "CapabilityRouter", "EchoProvider", "Request", "Result", "Constraints",
    "RealityGrader", "Hypothesis", "Verdict", "JUDGE_VERSION", "Telemetry", "seed_policies",
    "PlanningSubsystem", "ExecutionSubsystem", "ValidationSubsystem", "MemorySubsystem",
    "GovernanceSubsystem", "build_default_kernel",
]


def build_default_kernel() -> CognitiveKernel:
    """Wire a kernel with the five subsystems, the seed policies, and the offline EchoProvider."""
    k = CognitiveKernel()
    k.register_provider(EchoProvider())
    k.register_subsystem(PlanningSubsystem(router=k.router))
    k.register_subsystem(ExecutionSubsystem(workspace=k.workspace))
    k.register_subsystem(ValidationSubsystem())
    k.register_subsystem(MemorySubsystem())
    k.register_subsystem(GovernanceSubsystem())
    for policy in seed_policies():
        k.register_policy(policy)
    return k
