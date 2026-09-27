---
name: dsh-find-simplifications
description: Find evidence-backed simplifications in repository code, APIs, configuration, tests, and prose; write or consolidate proposals, identify small inline cleanups, or assess simplifications from another branch. Use for removing dead, duplicated, speculative, or unnecessarily maintained behavior and infrastructure.
---

# Finding Repository Simplifications

Find changes that remove maintained obligations: APIs, representations, lifecycle states, configuration paths, dependencies, tests, or documentation. Prefer a few well-supported candidates over a count of deletions. This is guidance, not a checklist; keep the user's scope and distinguish a survey from permission to implement its proposals.

## Establish scope and constraints

Read the root instructions, [architecture](../../../docs/architecture.md) before judging structure, and [testing policy](../../../docs/testing.md). Consult the relevant active Agent Notes for intentional decisions; use the [note rules](../../notes/README.md) for new records. Archived notes are historical examples, not current authority: never inspect, verify, or repair their outbound links.

Treat designs that an active Agent Note deliberately protects as constraints unless the user explicitly overrides them. Unused members within a protected design remain candidates when their removal preserves its purpose.

For broad requests, divide independent domains among subagents, give each a bounded domain, and require consumer evidence and rejected alternatives. If subagents are unavailable, cover the same breadth yourself. Inspect substantial production machinery as well as obvious unused symbols; do not stop after the first promising deletion.

## Search for removable obligations

Use these questions to guide discovery:

- **Does a declared feature have a complete effect path?** Trace producer, transformations, provider or endpoint support, and observable result. A field copied everywhere may still have no setter, no reader, or only implementations that reject it. Search constructors and discriminant emitters as well as callers. Zero fixed callers is weaker evidence than unreachability: a deliberate extension path can have no repository call sites.
- **Which distinctions change a consumer's action?** Several internal states may require one public status or one usable identifier. Keep internal distinctions that control authorization, residency, durability, or ownership; remove public distinctions that only invite an unusable choice. Do not erase distinct durable facts merely because one renderer ignores them.
- **Could a smaller explicit behavior remove the subsystem?** Fixed intervals, caller-supplied parameters, or reported failure can eliminate generalized schedulers, persisted defaults, or automatic rollback. Name the capability given up and the machinery deleted. A production caller makes this a behavior decision, not an automatic rejection; implementation must remain within the user's authorization.
- **Can a consumer read the authoritative value when needed?** Look for copied histories, promotion ledgers, invalidation events followed by reads, and feature caches beside a shared source. Derivation or reuse may delete subscriptions, retained data, stale-response handling, and recovery paths together. Establish the required time of observation first; independent user state cannot be derived.
- **Is composition being mistaken for policy?** Optional service presence, a provider method, or a sibling feature can express availability without deciding deployment behavior. Explicit configuration or a caller-intent operation may remove registries and dependency checks. Preserve distinct operations when their ownership or completion timing differs.
- **What owns the complete maintenance cost?** Trace pass-through configuration, duplicate application trees, demo launchers used by products, resolver-only workspaces, and installation helpers with their own upgrade lifecycle. Compare the entire removed system with the replacement, including residual glue; moving complexity or adding a gate to keep duplicate definitions equal does not remove it.

## Prove reachability and the trade-off

Start with `rg`, then read the matches. Search exact symbols, property reads and writes, discriminants, event and wire strings, config keys, package names, and both `.method(` and `method(` forms. Tests and declarations can show a contract without proving a shipped producer or consumer.

Include source, runtime scripts, shipped configuration, package manifests and exports, loader resolution, generated runtime assets, and installed-package consumers. Classify examples and fixtures by their actual entry point rather than directory name. Follow generated catalogs to their consumers: a catalog read at runtime is a dynamic product API, while a documentation-only listing is not a fixed caller. Unused-code tools generate candidates, not deletion proof.

For each candidate, record the current owner, effective producer/consumer path, what disappears, what remains, and the strongest reason to retain it. Distinguish:

- removal of unreachable or unread behavior;
- a narrower public or product behavior with an explicit loss;
- a protected obligation or insufficient evidence.

Reject a candidate when it breaks a retained obligation, merely relocates the same complexity, or has no meaningful reduction. Read rejection reasons at the level of the proposed change: a stale inventory or a mixed proposal's rejected behavior does not settle every independent item, and a past rejection is a scoped falsifier, not a permanent ban. Refresh the evidence before re-proposing one. Small local improvements belong in actionable `TODO`/`FIXME`/`XXX` comments, not standalone design records.

## Preserve ownership and failure semantics

For copies, freezes, validators, and callback captures, name the value's origin, next owner, and trust boundary. Typed same-process calls ordinarily borrow readonly values; parsers, config loaders, queues, model/tool JSON, durable files, workers, processes, and wire decoders own or validate their inputs. Hostile-getter or callback-replacement tests do not establish a requirement by themselves. A frozen root does not prove its descendants immutable, and equal ids do not prove object identity.

For asynchronous machinery, map each promise, flag, cancellation path, disposer, and reservation to its owner and transition. Collapse mechanisms only when they express the same fact. Preserve synchronous publication and rollback, callback containment, first-terminal-outcome arbitration, worker/process ownership, and dispose-to-quiescence where required. Durable start/end markers can record real facts even when renderers ignore them; dropping interrupted work is a capability loss, not redundant-log cleanup.

A runtime consistency check is justified by comparing independently produced observations that can diverge. Checks of service presence, metadata, fixed examples, or the same mutation's return value do not qualify.

## Replace infrastructure only for a net reduction

Introducing a dependency is a valid simplification. Search existing dependencies and platform builtins at the supported runtime floor before adding a package. Identify the exact implementation and dedicated tests the replacement deletes, its maintenance and transitive cost, and every residual behavior the glue must preserve.

Exercise the mismatches most likely to defeat the replacement: protocol truncation, cancellation and teardown, configured bounds, deterministic test clocks, platform packaging, and source versus built entry points. A library that covers framing but requires rebuilding the same framing to enforce a size limit is not a simplification. An accepted edge-behavior change belongs in the proposal and relevant tests. Do not re-prove a dependency's generic specification while omitting tests for the repository-specific shim.

## Record, consolidate, and validate

Use [dsh-prose-standard](../dsh-prose-standard/SKILL.md) when prose is in scope. Remove code-restating or remotely owned explanations while preserving local behavior, timing, ownership, and failure obligations. Update affected READMEs, JSDoc, catalogs, configuration, snapshots, and generated files with their owning change.

A substantial proposal uses the mandatory note skeleton: `Problem`, `Proposal`, `Alternatives considered`, `Acceptance criteria`, and `Risks`. Include concrete consumer evidence, the removed maintenance cost, the capability given up, and observable acceptance conditions. An implemented decision uses the [implemented format](../../notes/README.md#the-body-skeleton) instead. Update an existing owner when the decision is the same; do not create duplicate notes to preserve candidate counts.

Every new note requires the scoped [supersession check](../../notes/AGENTS.md); the [Agent Note rules](../../notes/README.md#archiving-and-deletion) own retention, consolidation, deletion, and frozen archive mechanics. A code survey does not imply a repository-wide note audit. Preserve partial supersessions and current durable, wire, compatibility, or rejected-alternative obligations.

When folding another branch, compare its independent diff against the target base, port only supported non-overlapping proposals, and consolidate overlapping rationale. Closing another PR requires authorization or clear ownership of that housekeeping.

Select checks using [the root testing policy](../../../AGENTS.md#run-relevant-checks-locally); for Agent Note edits, include `python3 scripts/verify_agent_notes.py`. Report the surveyed areas, supported candidates, meaningful rejections or deferrals, notes added/consolidated/retained/removed, and commands actually run. Do not describe an unverified search as exhaustive.
