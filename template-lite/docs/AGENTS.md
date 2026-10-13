# AGENTS.md — Documentation

This file applies to `docs/` alongside the root `AGENTS.md`.

## Ownership

| Location | Owns |
| --- | --- |
| `specs/` | Current state in present tense: [architecture.md](specs/architecture.md) maps composition and cross-subsystem flows; every other page is one subsystem's reference, indexed with its [page rules](specs/README.md#page-rules). |
| `decisions/` | ADRs: durable choices, rejected alternatives, and consequences. |
| `tasks/` | Task briefs: bounded scope, constraints, acceptance, and the checks that actually ran. |

## Rules

- Give each fact one owning document and link to it elsewhere. Essential behavior, failure, and ownership facts may repeat at the point of use when a local contract needs them.
- Update the owner before dependent summaries or briefs.
- Specs describe the current system. Replace stale claims in place; do not append history or name the task that introduced a behavior. Planned behavior stays in a task brief or ADR until it ships; a spec never lists what is not built yet.
- Write an ADR only when a future agent would otherwise likely reverse the decision. Mechanical and small local edits need none. Update an existing ADR's owner instead of duplicating it; supersede a reversed decision with a new ADR and link both.
- Write a task brief only for work that spans sessions or needs agreed constraints. Small changes need none.
- Size budgets: a task brief fits in about 60 lines, including its result; an ADR fits in about 50. Longer means the document prescribes implementation steps, phases, or test matrices the implementing agent should choose. Split independent work into separate briefs.
- Completed briefs are history. Move any still-binding rule into a spec or ADR; current docs must not depend on a brief.
- Record only checks that actually ran.
- Keep rationale that prevents a likely mistake; remove narration, repeated background, speculative checklists, and chat transcripts.
- One physical line per paragraph. Link repository references with relative Markdown paths.

Start new documents from [the ADR template](decisions/TEMPLATE.md) or [the task template](tasks/TEMPLATE.md). Use [the prose standard](../.agents/skills/dsh-prose-standard/SKILL.md) for substantial writing or review.
