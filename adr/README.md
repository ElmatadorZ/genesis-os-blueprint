# Architecture Decision Records

An ADR captures **one architectural decision**, the forces behind it, and its consequences — so
that a year later, someone (including you) can understand *why* the system is shaped the way it is,
not just *that* it is.

## Rules of the house

1. **One decision per record.** If you are deciding two things, write two ADRs.
2. **Immutable once Accepted.** You do not edit an accepted ADR to change the decision; you write a
   new ADR that **supersedes** it, and mark the old one `Superseded by ADR-XXXX`.
3. **Status is explicit.** `Proposed → Accepted → (Superseded | Deprecated)`. An agent may author a
   `Proposed` ADR; only the human principal moves it to `Accepted` (the amendment ceremony, docs §06).
4. **Consequences are honest.** Every decision has downsides. An ADR with only upsides is a sales
   pitch, not a record.

## How to add one

```bash
cp ADR-TEMPLATE.md ADR-0004-my-decision.md
# edit; open a PR; leave it Proposed until the principal ratifies.
```

## Index

| ADR | Title | Status |
|---|---|---|
| [0001](ADR-0001-cognitive-kernel.md) | Adopt a Cognitive Kernel with a plugin ABI | Accepted |
| [0002](ADR-0002-capability-provider.md) | Model/resource as a swappable Capability Provider | Accepted |
| [0003](ADR-0003-reality-grading.md) | Grade missions against reality, not self-report | Accepted |
