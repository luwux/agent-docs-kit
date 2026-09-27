---
name: dsh-prose-standard
description: Use when writing, reviewing, restoring, or trimming substantial prose in a repository, including Markdown docs, JSDoc, code and test comments, prompts, diagnostics, and CLI or UI strings, or when deciding where such prose is required.
---

# Repository Prose Standard

Write enough to preserve the contract, then remove reasoning transcripts, repetition, and decoration. A contract is an obligation, invariant, precondition, postcondition, or compatibility promise that a caller, implementer, producer, or consumer relies on. Use [the documentation guide](../../../docs/AGENTS.md) for placement. This skill is guidance, not a mandatory pass for routine code changes.

Review tasks report findings without editing; explicitly requested write, fix, or trim tasks apply clear changes.

## Preserve the complete proposition

Before trimming or rewriting, preserve every relevant:

- actor and action;
- condition, timing, and ordering;
- must, may, and never requirement;
- ownership, side effect, failure mode, and consequence;
- compatibility promise, exception, and negative guarantee.

Shorter text is not better when it drops one of these facts. Keep non-obvious rationale when its absence could cause misuse or an incorrect simplification; otherwise state the rule and link the owning spec or ADR.

## Put prose in the right place

- Specs state current behavior and interfaces; ADRs explain durable choices and rejected alternatives; task briefs constrain bounded work.
- Public JSDoc documents caller-visible return distinctions, throws or rejections, side effects, ownership, timing, cancellation, and durability.
- Internal comments explain non-obvious invariants, race ordering, ownership, security boundaries, and surprising failure behavior. Do not narrate control flow or restate code.
- Test comments explain only a non-obvious fixture, platform accommodation, entry path, or indirect observation.
- READMEs state the consumer contract: configuration, semantics, failures, and limitations.
- Prompts, diagnostics, CLI output, and visible strings are behavior. Diagnostics name the failing subject, the violated rule, and the correction when it is non-obvious.

Generated or derived artifacts are not owners. Change the owning source first.

## Workflow

1. Read the owning code or document before judging a passage.
2. Classify each candidate as keep, add, trim, restore, restructure, or defer. Add prose when code and types do not carry a required contract.
3. Apply only proposition-preserving changes; do not manufacture edits to meet a deletion target.
4. Re-check nearby analogous prose after learning a rule.
5. Report the inspected scope, changes, deliberate keeps, deferred cases, and checks actually run.

Do not create a new document, historical appendix, or repository-wide prose audit unless the task requires one.
