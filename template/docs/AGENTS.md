# AGENTS.md — Documentation

This file applies to `docs/` alongside the root `AGENTS.md`.

## Layout

| Location | Holds | Changes |
| --- | --- | --- |
| [architecture.md](architecture.md) | The root map: how subsystems compose, flows that cross them, shared rules, and the table of root pages | With the code |
| `specs/` | One page per subsystem: current behavior and known limitations. A page with parts grows into a node (see [Specs](#specs)) | With the code, in the same change |
| [product.md](product.md) | Scope, goals, non-goals, and direction | When the direction changes |
| `decisions/NNNN-title.md` | Why a durable choice was made | Not after acceptance; a reversal is a new decision |
| `tasks/NNNN-title.md` | Bounded work: goal, scope, constraints, acceptance, result | While open; frozen once done or dropped |
| `research/YYYY-MM-DD-title.md` | Dated evidence: measurements, experiments, comparisons with other projects | Never; newer evidence is a new file |
| Other `docs/*.md` | Current-state topics that span subsystems, such as testing, deployment, or an upstream adaptation | With the code |

## Rules

1. Current-state documents (architecture maps, specs, and topic documents) describe what exists now. Replace a stale statement in place; do not append history or name the change that introduced a behavior.
2. Each fact has one home; link to it elsewhere. A local contract may repeat an essential behavior, failure, or ownership fact where it is used.
3. Current-state documents never list unbuilt behavior. Planned work lives in a task, the direction in [product.md](product.md), and the reason for a choice in a decision. When work ships, its behavior moves into the spec.

## Specs

A spec describes one subsystem as built. A subsystem is a single page until it has parts; then it becomes a node, a folder shaped like `docs/` itself, so a node can split again.

- **When code needs a page:** write a spec for code an agent must understand before editing it safely: an interface other code relies on, state or a data format, or invariants and failure handling spread across files. Small self-contained code, such as one-off scripts, needs no page: its header comment or `--help` documents it, and a topic document such as `development.md` may list the commands, one line each. Code no page owns is normal.
- **New code:** a feature that extends a subsystem goes on that subsystem's page: add its files to the `Source:` and describe it where it fits. Start a new page only when the new code meets the bar above on its own.
- **Page:** `specs/<name>.md`, named in kebab-case. The first line after the title is `Source:` followed by the backticked repository paths the page owns, for example ``Source: `src/sync/`, `src/storage/schema.ts`, `publish/src/render-*.ts` ``. A directory path ends with `/`; in a glob, `*` stays within one path segment and `**` crosses segments; a path that exists on disk is literal even when it contains `[`, `*`, or `?`, such as `app/media/[...key]/`. Each path is declared once, except as Ownership allows. A cross-cutting page that owns no code, such as privacy rules that span subsystems, writes `Source: none`.
- **Node:** `specs/<name>/` holds only `architecture.md` and its own `specs/` folder. Its `architecture.md` is the subsystem's page and its map: a `Source:` line covering every path of the subsystem, then the scope, the interface other subsystems rely on, a table linking each page in its `specs/` with its role, the flows between those pages, and the rules and limitations they share. Decisions, tasks, and research stay in the root `docs/`.
- **Root:** [architecture.md](architecture.md) is the root node's map: the same content without a `Source:` line.
- **Ownership:** every page in a node declares only paths inside the node's `Source:`, and may repeat one of them exactly, such as a single file; the page then owns it. The most specific declaration owns a file: a file over a glob, a glob over a directory, a deeper directory over its parent. Files no page of a node claims belong to the node's `architecture.md`.
- **Maps:** each map's table lists every page of its node once, with the link in the first cell: `specs/<name>.md` or `specs/<name>/architecture.md`.
- **Link text:** name a page by its label, as the `AGENTS.md` table shows it (`cli`, `cli/shot`), or by its subject, not by its file name: a split changes the file name but not the label. Generated tables follow the same rule.
- **Content:** open with one scope paragraph: what the subsystem owns, which subsystems it calls or is called by (linked), and what it does not own. Then document what applies: data and types, behavior and lifecycle, failure and recovery, configuration, extension points, known limitations, and the checks to run after changing it. Link the authoritative code instead of restating it. Flows between sibling pages belong in their node's map.
- **Pointers:** one entry file of each owned directory, such as the package comment, the main type, or the `index` module, carries one comment naming its page by repository path, for example `// Spec: docs/specs/sync.md`. Files that cannot hold comments, such as JSON, need none.
- **Check:** `python3 scripts/verify_subsystem_pages.py` checks the tree, its links and their `#anchors`, and the generated table in the root `AGENTS.md`, and prints notes for pages over about 4,000 words and maps over about 3,000. `--map` regenerates the table after a `Source:` line changes; `--owner <path>` names a path's page; `--changed [BASE]` lists pages whose owned paths changed while the page did not; `--pointers` lists pages that no owned file names; `--refs <page>` lists every link to a page and every mention of its path, in code and records too, grouped by anchor, and marks anchors the page no longer has; `--split` and `--move` are described under [Splitting a page](#splitting-a-page).

### Splitting a page

Split a page when both hold: it exceeds about 4,000 words, and its content falls into at least three parts that own different files and are edited independently. A long page about one tightly coupled part is condensed instead: dated measurements move to research and rationale to a decision.

- Parts of one subsystem become a node. `python3 scripts/verify_subsystem_pages.py --split docs/specs/<name>.md` moves the page to `specs/<name>/architecture.md`, rewrites links and pointer comments to it, and lists other mentions of `<name>.md` to review, such as link text or the strings a generator turns into links. A file the script rewrote may be generated; change its source and regenerate it. Then give each part a page in `specs/<name>/specs/`, cut along files that change together, and keep in `architecture.md` only what every part needs.
- Create each part's page with its title and `Source:` line, list it in the node's map, and move sections onto it with `--move docs/specs/<name>/architecture.md#<anchor> docs/specs/<name>/specs/<part>.md`. The command appends the section with its subsections, fixes the relative links inside it, and retargets every link and path mention of its anchors, except plain text in finished records. Text moved by hand breaks links to its anchors: the default check reports those inside the spec tree, and `--refs <page>` lists the rest, in code, tasks, and other documents.
- A file that serves several parts, such as a command dispatcher or a shared registry, stays with the node: leave it out of the parts' `Source:` lines, so the node's `architecture.md` owns it.
- Moving a page fixes links to it everywhere, records included, because a link only navigates. Plain-text mentions in finished tasks, decisions, and research stay as written: they record what existed then.
- A part that is really a separate subsystem becomes a sibling page in the same folder instead.
- Each part is a page under the same rules, so it splits again only when it meets both conditions above. A split moves text as it is: a part about one file that stays long keeps its note, and condensing it is separate work. A part under about 400 words joins a neighbor unless it owns separate code. A node left with one page turns back into a single page.

## When to write each

- **Decision**: when a future agent would likely reverse a choice without knowing why, or when the user decided something the code does not make obvious. Mechanical and small local edits need none. Aim for about 50 lines. An accepted decision is not edited; to reverse it, write a new decision and change the old one's status line to `Superseded by NNNN`.
- **Task**: for work that spans sessions or needs agreed constraints; small changes need none. Its status is `Open`, `Done`, or `Dropped`; fill in the result when the work ends. A finished task is history: move any rule that still binds into a spec or decision, because current-state documents never depend on a task. Aim for about 60 lines; split independent work into separate tasks.
- **Research**: when evidence behind a decision or spec would be costly to reproduce. Name the date and the code version it measured. It does not describe current behavior; specs and decisions link it.
- Decisions and tasks are numbered with four digits in creation order. Start from [the decision template](decisions/TEMPLATE.md) or [the task template](tasks/TEMPLATE.md).

## Writing

- Record only checks that actually ran.
- Keep what prevents a likely mistake; drop narration, repeated background, and transcripts.
- One physical line per paragraph. Link repository references with relative Markdown paths.
