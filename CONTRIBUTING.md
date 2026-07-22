# Contributing

Thanks for considering a contribution. This repository is a **reference blueprint**, so the
bar for changes is a little different from a typical library: the goal is *clarity and
correctness of the architecture*, not feature count.

## Principles (please read before opening a PR)

1. **Every change must increase either reliability or evidence.** A change that adds capability
   without adding a way to hold that capability accountable is, by this repo's own law, a
   regression. See the load-bearing law in the [README](README.md).
2. **The reference stays dependency-free.** `genesis_kernel/` must import only the Python
   standard library. Provider integrations (real LLMs, cloud APIs) belong in *your* fork or in a
   clearly separated `contrib/` example, never in the core.
3. **Contracts change by ADR, code changes by PR.** If you are altering the Kernel ABI, the
   Policy Hook contract, or the Capability contract, open an ADR first (copy
   [`adr/ADR-TEMPLATE.md`](adr/ADR-TEMPLATE.md)) so the *why* is recorded, then implement it.
4. **Fail-closed is not negotiable.** Any change to the Policy Hook Surface must preserve the
   invariant that an error in a policy denies the action. Tests must prove it.
5. **Docs and reference move together.** If you change a lifecycle rule in the reference, update
   the matching `docs/` and `specs/` file in the same PR, or the blueprint lies.

## Workflow

1. Open an issue describing the problem or the decision. For architectural changes, draft the ADR
   in that issue.
2. Fork, branch, implement. Keep the diff focused — one concept per PR.
3. Run the checks locally:
   ```bash
   cd reference
   python examples/run_mission.py       # must complete and print a full audit trace
   python tests/test_kernel.py          # must be all-green and fully offline
   ```
4. Open the PR. Describe which invariant your change protects or strengthens.

## What we will decline

- Bundling a specific model vendor into the core.
- Anything that lets a subsystem write "success" without evidence (it breaks Reality Grading).
- Removing an audit record or a fail-closed guard "for performance."

## License of contributions

By submitting a contribution you agree it is licensed under the **Apache License 2.0**, the same
license as the project. See [LICENSE](LICENSE).
