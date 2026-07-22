"""
genesis_kernel.providers — the Capability Provider model + Router.

Normative spec: ../../specs/capability-contract.md. The model/GPU/human is a swappable provider
of a capability; the router picks one deterministically and never fabricates a result.

Ships a deterministic, offline EchoProvider so the whole reference runs with no network and no
API key — the same discipline as the search Provider Layer (keyed first, free fallback,
no-key path unchanged).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .abi import Capability
from .telemetry import Telemetry


@dataclass
class Constraints:
    sovereign: bool = False       # if True, data may NOT leave the box (hard constraint, IN1)
    deterministic: bool = False   # if True, prefer a reproducible provider (IN2)
    max_cost: Optional[float] = None


@dataclass
class Request:
    capability: Capability
    payload: Dict[str, Any] = field(default_factory=dict)
    constraints: Constraints = field(default_factory=Constraints)


@dataclass
class Result:
    ok: bool
    output: Any
    provider: str
    meta: Dict[str, Any] = field(default_factory=dict)


class CapabilityProvider(ABC):
    """PR1-PR3: attributable, availability-gated, capability-scoped."""
    name: str = "provider"
    provides: List[Capability] = []
    leaves_box: bool = False      # does invoking move data off-box? (sovereignty gate)
    deterministic: bool = True    # can it guarantee a reproducible result?

    def available(self) -> bool:  # AV1: cheap, side-effect-free; False -> skipped, not errored
        return True

    @abstractmethod
    def invoke(self, capability: Capability, request: Request) -> Result:
        raise NotImplementedError


class EchoProvider(CapabilityProvider):
    """Deterministic offline stand-in for a model. Reproducible by construction."""
    name = "echo-local"
    provides = [Capability.REASONING, Capability.PLANNING,
                Capability.VALIDATION, Capability.EXECUTION]
    leaves_box = False
    deterministic = True

    def available(self) -> bool:
        return True

    def invoke(self, capability: Capability, request: Request) -> Result:
        if capability not in self.provides:                      # PR2
            return Result(False, None, self.name, {"reason": "capability not provided"})
        goal = request.payload.get("goal", "")
        if capability is Capability.REASONING:
            out = f"reasoned over goal ({len(goal)} chars): proceed step-wise"
        elif capability is Capability.PLANNING:
            out = [s.strip() for s in goal.split(";") if s.strip()] or ([goal] if goal else [])
        elif capability is Capability.VALIDATION:
            out = bool(request.payload.get("results"))
        else:  # EXECUTION
            out = "executed"
        return Result(True, out, self.name, {"deterministic": True})


class CapabilityRouter:
    """Deterministic, auditable, never-fabricating selection (capability-contract §5)."""
    def __init__(self, providers: Optional[List[CapabilityProvider]] = None,
                 telemetry: Optional[Telemetry] = None) -> None:
        self._providers: List[CapabilityProvider] = list(providers or [])
        self._telemetry = telemetry

    def register(self, provider: CapabilityProvider) -> None:
        self._providers.append(provider)

    def _skip(self, cap: Capability, provider: str, reason: str) -> None:
        if self._telemetry is not None:
            self._telemetry.emit("routing", capability=cap.value, provider=provider,
                                 ok=False, skipped=reason)

    def route(self, request: Request) -> Result:
        cap = request.capability
        for p in self._providers:                                # RT1: deterministic order
            if cap not in p.provides:
                continue
            if not p.available():                                # AV1: skip, not error
                self._skip(cap, p.name, "unavailable")
                continue
            if request.constraints.sovereign and p.leaves_box:   # IN1: sovereignty is hard
                self._skip(cap, p.name, "sovereignty: provider leaves box")
                continue
            if request.constraints.deterministic and not p.deterministic:  # IN2
                self._skip(cap, p.name, "non-deterministic under deterministic constraint")
                continue
            result = p.invoke(cap, request)
            if self._telemetry is not None:                      # RT2: record the choice
                self._telemetry.emit("routing", capability=cap.value, provider=p.name, ok=result.ok)
            if result.ok:
                return result
        # RT3: explicit failure, never a fabricated result
        return Result(False, None, "*", {"reason": "no provider could serve"})
