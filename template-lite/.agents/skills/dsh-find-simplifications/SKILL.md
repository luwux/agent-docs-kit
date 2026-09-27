---
name: dsh-find-simplifications
description: Use only when explicitly asked to simplify, remove dead code, reduce duplication, or audit over-built infrastructure; finds evidence-backed candidates without treating static-analysis output as proof.
---

# Finding Repository Simplifications

Use this skill only when the user or task explicitly asks for it. Ordinary feature work must not expand into a repository-wide cleanup. Review tasks are read-only unless implementation is explicitly authorized.

Read [the architecture spec](../../../docs/specs/architecture.md) and applicable ADRs before judging a candidate; a simplification that fights a recorded decision needs extra evidence.

## Strong candidates

Prefer a few well-proven candidates whose removal or consolidation produces a real net reduction:

- a public function, event, config option, component, or helper has no production consumer;
- tests or docs are the only consumers and protect no durable compatibility obligation;
- two maintained representations mirror the same fact;
- an abstraction exposes generality that no caller uses;
- hand-rolled code reimplements a platform builtin or a healthy, well-maintained dependency, and the swap deletes the implementation plus its dedicated tests;
- several flags, promises, or state variables in asynchronous code mirror the same liveness or settlement fact.

Complexity alone is not evidence. A wrapper that relocates the same behavior is not a simplification.

## Required evidence

Use `rg` with the exact symbol, event name, config key, and wire string, then read the call sites. Classify consumers as production, non-production (tests, docs, fixtures), dynamic or platform entry point, or ambiguous. Unused-code tools generate candidates, not deletion proof.

Before removing code, check runtime entry points and bindings, persisted and wire formats, migrations, service workers and caches, scripts, and configuration loaders.

Reject or downgrade a candidate when a production or compatibility consumer exists (that is a product change, not cleanup), when an ADR justifies it and the new evidence does not beat that reason, or when the gain is tiny.

## Output

- Report the strongest candidates with exact owners, consumers, expected net deletion, behavior given up, and residual risk.
- Do not create ADRs, task briefs, or speculative TODOs merely because an audit found an idea. Record durable work only after the user approves it.
- If implementation is authorized, choose checks with the [root testing policy](../../../AGENTS.md#run-relevant-checks-locally) and report only checks that actually ran.
