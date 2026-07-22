"""
genesis_kernel.reality_grading — the honesty loop.

Normative doc: ../../docs/05-reality-grading-loop.md · ADR-0003. A completed mission stakes a
falsifiable hypothesis; a versioned judge grades it against EVIDENCE (an evidence query that reads
reality), never against the model's claim of success (Evidence Normalization).
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from .telemetry import Telemetry

JUDGE_VERSION = "rg-1"   # existence/predicate-based. A change to this is a governed act (Migration Note).


@dataclass
class Hypothesis:
    id: str
    statement: str
    evidence_query: Callable[[], bool]   # reads reality; returns True iff reality confirms
    judge_version: str = JUDGE_VERSION   # pinned at stake time — history is immutable
    staked_at: float = field(default_factory=time.time)
    horizon_s: float = 0.0               # when it becomes gradable (the Outcome Clock)


@dataclass
class Verdict:
    hypothesis_id: str
    status: str                          # "confirmed" | "refuted" | "abstain"
    judge_version: str
    evidence_hash: Optional[str] = None  # immutable evidence on a Validated Episode


class RealityGrader:
    def __init__(self, telemetry: Optional[Telemetry] = None) -> None:
        self._staked: Dict[str, Hypothesis] = {}
        self._episodes: List[Verdict] = []   # confirmed = Validated Episodes
        self._telemetry = telemetry

    def stake(self, statement: str, evidence_query: Callable[[], bool],
              horizon_s: float = 0.0) -> Hypothesis:
        hid = "pr_" + hashlib.sha256(statement.encode("utf-8")).hexdigest()[:12]
        h = Hypothesis(hid, statement, evidence_query, JUDGE_VERSION, time.time(), horizon_s)
        self._staked[hid] = h
        if self._telemetry is not None:
            self._telemetry.emit("outcome", status="STAKED",
                                 detail=f"{hid} @ {JUDGE_VERSION}: {statement}")
        return h

    def grade(self, hypothesis: Hypothesis, evidence_available: bool = True) -> Verdict:
        """Evidence Normalization: we CALL the evidence query (reads the world). We never read a
        model's claim. If evidence can't be gathered, we abstain; if the query errors, fail-closed
        to 'refuted' (an unverifiable success is not a success)."""
        if not evidence_available:
            v = Verdict(hypothesis.id, "abstain", hypothesis.judge_version)
        else:
            try:
                confirmed = bool(hypothesis.evidence_query())
            except Exception:
                confirmed = False   # fail-closed: cannot verify -> not confirmed
            if confirmed:
                ehash = hashlib.sha256(
                    f"{hypothesis.id}:confirmed:{hypothesis.judge_version}".encode()).hexdigest()[:16]
                v = Verdict(hypothesis.id, "confirmed", hypothesis.judge_version, ehash)
                self._episodes.append(v)   # immutable Validated Episode
            else:
                v = Verdict(hypothesis.id, "refuted", hypothesis.judge_version)
        if self._telemetry is not None:
            self._telemetry.emit("outcome", status=f"GRADED:{v.status}",
                                 detail=f"{hypothesis.id} @ {v.judge_version}"
                                        + (f" evidence={v.evidence_hash}" if v.evidence_hash else ""))
        return v

    def validated_episodes(self) -> List[Verdict]:
        return list(self._episodes)

    def vital_signs(self) -> Dict[str, object]:
        """Honest health API: unknowns render as 'no data yet', never fake zeros."""
        staked = len(self._staked)
        return {
            "hypotheses_staked": staked,
            "validated_episodes": len(self._episodes),
            "judge_version": JUDGE_VERSION,
            "status": "no data yet" if staked == 0 else "live",
        }
