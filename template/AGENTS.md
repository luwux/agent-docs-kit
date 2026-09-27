# AGENTS.md

Preserve existing unrelated edits. Subtree `AGENTS.md` files supplement these repository-wide conventions for their scope.

Read [docs/architecture.md](docs/architecture.md) before changing architecture; follow [docs/AGENTS.md](docs/AGENTS.md) for documentation. **Testing policy** — [docs/testing.md](docs/testing.md).

## Run relevant checks locally

- Use your judgment to choose the minimum necessary tests for the change. Avoid redundant tests or reruns; skip testing when unnecessary.
- Report only commands actually run and their actual results. Report pending checks as pending, and inspect failures before attributing them to the change or the environment.

## Conventions

- Non-trivial changes must include an Agent Note in the same change, because code and docs cannot carry the rationale and rejected alternatives; update the owning note or add one, with [mechanical/local exemptions](.agents/notes/README.md#when-to-write-one). Archived notes are frozen: never edit or treat them as current authority ([archive policy](.agents/notes/archived/AGENTS.md)).
- **Tests describe behavior, not correctness.** Change obsolete behavior with its tests; record the reason in the owning Agent Note when the change is non-trivial.
- Treat generated catalogs, snapshots, and fixtures as derivative. Edit the owning source or scenario first, then regenerate the artifact.
- Files end with exactly one trailing newline.

## Documentation

Comments and docs state complete contracts and context, not reasoning transcripts. Use direct, concrete terms. Do not use metaphors. Before writing `contract`, `boundary`, or `shape`, ask whether a more exact term names the subject: write `response fields`, `JSON validation`, or `ESM exports` instead of `response shape`, `validation boundary`, or `module shape`. Keep `contract` for preconditions, postconditions, invariants, compatibility promises, and other obligations that callers, callees, implementers, providers, producers, or consumers rely on. Keep a literal process, wire, security, transaction, or lifecycle boundary. Do not narrate control flow or tests, preserve review history, or restate code. Keep behavior, failure, timing, ownership, and safe-use facts; link the rationale. Use [the prose standard](.agents/skills/dsh-prose-standard/SKILL.md) for decisions. Use narrow, justified exceptions instead of disabling a rule globally.

Update affected READMEs, API documentation, and comments when behavior or contracts change. Current-state prose, one physical line per paragraph, and one home per fact live in [docs/AGENTS.md](docs/AGENTS.md).

## Editing these instructions

When `CLAUDE.md` symlinks an `AGENTS.md`, edit the real file. Keep each rule self-contained while linking high-level docs. Condense when clarity survives.
