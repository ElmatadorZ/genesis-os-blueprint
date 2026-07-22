"""Governance subsystem — deliberation + policy authoring (Capability.GOVERNANCE).

An agent may PROPOSE an amendment; only the human principal may RATIFY (docs §06). This subsystem
models the propose side; ratification is represented as a human-provider decision the kernel does
not grant itself.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from ..abi import Capability, Context, Event, Subsystem


@dataclass
class Amendment:
    proposer: str
    text: str
    status: str = "proposed"          # proposed -> accepted (only by principal) | rejected
    migration_note: str = ""


class GovernanceSubsystem(Subsystem):
    name = "governance"
    provides = [Capability.GOVERNANCE]

    def __init__(self) -> None:
        self.amendments: List[Amendment] = []

    def handle(self, event: Event, ctx: Context) -> Optional[Event]:
        return None

    def propose(self, proposer: str, text: str, migration_note: str = "") -> Amendment:
        a = Amendment(proposer=proposer, text=text, migration_note=migration_note)
        self.amendments.append(a)
        ctx = None  # proposal itself takes no run budget
        return a

    def ratify(self, amendment: Amendment, principal: str) -> Amendment:
        """Only a human principal may call this. The kernel never ratifies its own proposals."""
        amendment.status = "accepted"
        amendment.text += f"\n[ratified by principal: {principal}]"
        return amendment
