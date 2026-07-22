"""
genesis_kernel.abi — the core types of the Cognitive Kernel ABI (v0.2).

Normative spec: ../../specs/kernel-abi.md. This module is the runnable oracle for that spec.
Everything here is standard-library only, by design (see CONTRIBUTING.md).
"""
from __future__ import annotations

import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

ABI_VERSION = "0.2"


class Capability(str, Enum):
    """The closed set of cognitive capabilities (kernel-abi §1.3)."""
    REASONING = "reasoning"
    PLANNING = "planning"
    MEMORY = "memory"
    EXECUTION = "execution"
    VALIDATION = "validation"
    GOVERNANCE = "governance"


class HookPoint(str, Enum):
    """The lifecycle points where the Policy Hook Surface fires (policy-hook-contract §1)."""
    PRE_PLAN = "PRE_PLAN"
    PRE_ACT = "PRE_ACT"
    PRE_VALIDATE = "PRE_VALIDATE"
    PRE_COMMIT = "PRE_COMMIT"
    PRE_RESPONSE = "PRE_RESPONSE"


class BudgetExceeded(Exception):
    """Raised by Context.spend when a step would overflow the token budget (kernel-abi K1)."""
    def __init__(self, requested: int, used: int, budget: int):
        super().__init__(f"budget exceeded: requested {requested}, used {used}, budget {budget}")
        self.requested, self.used, self.budget = requested, used, budget


@dataclass
class Event:
    """Immutable envelope + audit spine (kernel-abi §1.1)."""
    type: str
    payload: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    ts: float = field(default_factory=time.time)
    caused_by: Optional[str] = None

    def derive(self, type: str, **payload: Any) -> "Event":
        """Produce the next event in the chain, recording causation (S1: events are immutable)."""
        return Event(type=type, payload=payload, caused_by=self.id)


@dataclass
class Context:
    """Owns the token budget; guarantees never-overflow (kernel-abi §1.2, §3.1, K1)."""
    budget_tokens: int = 16384
    used_tokens: int = 0
    working_set: Dict[str, Any] = field(default_factory=dict)
    trace: List[str] = field(default_factory=list)

    def spend(self, n: int) -> None:
        if n < 0:
            raise ValueError("cannot spend negative tokens")
        if self.used_tokens + n > self.budget_tokens:
            raise BudgetExceeded(n, self.used_tokens, self.budget_tokens)
        self.used_tokens += n

    def remaining(self) -> int:
        return self.budget_tokens - self.used_tokens

    def log(self, msg: str) -> None:
        self.trace.append(msg)


@dataclass
class Decision:
    """A single policy verdict (policy-hook-contract §2)."""
    allow: bool
    reason: str
    policy: str


class Subsystem(ABC):
    """The plugin contract. Conformance is gated at load time by the kernel (kernel-abi §2, S1-S6)."""
    name: str = "subsystem"
    abi_version: str = ABI_VERSION
    provides: List[Capability] = []

    @abstractmethod
    def handle(self, event: Event, ctx: Context) -> Optional[Event]:
        """Pure-ish: (Event, Context) -> next Event, or None when the lifecycle is complete.
        MUST NOT perform an external side effect directly (S3); MUST spend budget (S4)."""
        raise NotImplementedError

    def conforms_to(self, abi_version: str) -> bool:
        """Load-time gate (S1/S2). MUST be side-effect-free and honest."""
        return self.abi_version == abi_version
