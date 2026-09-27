# AGENTS.md

Preserve existing unrelated edits. Subtree `AGENTS.md` files supplement these repository-wide conventions for their scope.

Read [docs/specs/architecture.md](docs/specs/architecture.md) before changing architecture; follow [docs/AGENTS.md](docs/AGENTS.md) for documentation.

## Run relevant checks locally

- Use your judgment to choose the minimum necessary tests for the change. Avoid redundant tests or reruns; skip testing when unnecessary.
- Report only commands actually run and their actual results. Report pending checks as pending, and inspect failures before attributing them to the change or the environment.

## Conventions

- Keep affected specs current in the same change. Write an ADR only when a future agent would otherwise likely reverse the decision; see [docs/AGENTS.md](docs/AGENTS.md#rules).
- **Tests describe behavior, not correctness.** Change obsolete behavior with its tests.
- Treat generated catalogs, snapshots, and fixtures as derivative. Edit the owning source first, then regenerate the artifact.
- Files end with exactly one trailing newline.

## Documentation

Comments and docs state complete contracts and context, not reasoning transcripts. Use direct, concrete terms. Do not narrate control flow or tests, preserve review history, or restate code. Keep behavior, failure, timing, ownership, and safe-use facts; link the rationale. Use [the prose standard](.agents/skills/dsh-prose-standard/SKILL.md) for substantial writing or review.
