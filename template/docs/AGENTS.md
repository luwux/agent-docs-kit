# AGENTS.md — Documentation

This file applies to `docs/` alongside the root `AGENTS.md`.

## Layout

| Location | Holds | Changes |
| --- | --- | --- |
| [architecture.md](architecture.md) | The map: how subsystems compose, flows that cross them, one entry per subsystem | With the code |
| [specs/](specs/README.md) | One page per subsystem: current behavior and known limitations | With the code, in the same change |
| [product.md](product.md) | Scope, goals, non-goals, and direction | When the direction changes |
| `decisions/NNNN-title.md` | Why a durable choice was made | Not after acceptance; a reversal is a new decision |
| `tasks/NNNN-title.md` | Bounded work: goal, scope, constraints, acceptance, result | While open; frozen once done or dropped |
| `research/YYYY-MM-DD-title.md` | Dated evidence: measurements, experiments, comparisons with other projects | Never; newer evidence is a new file |
| Other `docs/*.md` | Current-state topics that span subsystems, such as testing, deployment, or an upstream adaptation | With the code |

## Rules

1. Current-state documents (architecture, specs, and topic documents) describe what exists now. Replace a stale statement in place; do not append history or name the change that introduced a behavior.
2. Each fact has one home; link to it elsewhere. A local contract may repeat an essential behavior, failure, or ownership fact where it is used.
3. Current-state documents never list unbuilt behavior. Planned work lives in a task, the direction in [product.md](product.md), and the reason for a choice in a decision. When work ships, its behavior moves into the spec.

## When to write each

- **Decision**: when a future agent would likely reverse a choice without knowing why, or when the user decided something the code does not make obvious. Mechanical and small local edits need none. Aim for about 50 lines. An accepted decision is not edited; to reverse it, write a new decision and change the old one's status line to `Superseded by NNNN`.
- **Task**: for work that spans sessions or needs agreed constraints; small changes need none. Its status is `Open`, `Done`, or `Dropped`; fill in the result when the work ends. A finished task is history: move any rule that still binds into a spec or decision, because current-state documents never depend on a task. Aim for about 60 lines; split independent work into separate tasks.
- **Research**: when evidence behind a decision or spec would be costly to reproduce. Name the date and the code version it measured. It does not describe current behavior; specs and decisions link it.
- Decisions and tasks are numbered with four digits in creation order. Start from [the decision template](decisions/TEMPLATE.md) or [the task template](tasks/TEMPLATE.md).

## Writing

- Record only checks that actually ran.
- Keep what prevents a likely mistake; drop narration, repeated background, and transcripts.
- One physical line per paragraph. Link repository references with relative Markdown paths.
