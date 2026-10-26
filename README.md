# Agent Docs Kit

A documentation layout for repositories that coding agents work in. It gives every fact one home, keeps current-state pages separate from plans and history, and tells an agent which single page to read before it edits a file.

## Layout

| Location | Holds | Changes |
|---|---|---|
| `AGENTS.md` | Standing rules and a generated table from source paths to specs | Table regenerated when a `Source:` line changes |
| `docs/architecture.md` | The root map: how subsystems compose, the flows that cross them, and the table of pages | With the code |
| `docs/specs/` | One page per subsystem: current behavior and known limitations. A page with parts grows into a node shaped like `docs/` | With the code, in the same change |
| `docs/product.md` | Scope, goals, non-goals, and direction | When the direction changes |
| `docs/decisions/` | Why a durable choice was made, including dated user decisions | Not after acceptance; a reversal is a new decision |
| `docs/tasks/` | Bounded work: goal, scope, constraints, acceptance, result | While open; frozen once done or dropped |
| `docs/research/` | Dated evidence: measurements, experiments, comparisons | Never; newer evidence is a new file |

Three rules hold the layout together, stated in [`template/docs/AGENTS.md`](template/docs/AGENTS.md#rules):

1. Architecture, specs, and topic documents describe what exists now; stale statements are replaced, not appended to.
2. Each fact has one home; other documents link it.
3. Current-state documents never list unbuilt behavior: plans live in tasks and `product.md`, reasons in decisions.

## Install

Requires Python 3.9 or later. Preview first; nothing is written:

```bash
python3 init.py /absolute/path/to/project
```

Then apply:

```bash
python3 init.py /absolute/path/to/project --apply
```

Add `--claude-symlinks` to also create `CLAUDE.md -> AGENTS.md` links in the root and in `docs/`.

The initializer copies only the seven files listed in `init.py` and ignores platform files (`.DS_Store`, `Thumbs.db`, `*.pyc`, `__pycache__/`). It refuses the whole install, writing nothing, when the template holds any other unlisted file, a destination file already exists, or a destination directory is a symlink. For a repository that already has documentation, merge from [`template/`](template/) by hand.

After installing, `docs/architecture.md` and `docs/product.md` state that nothing is recorded yet. Audit the repository and write the architecture map, the product page, and one spec per subsystem before treating the adoption as complete.

## Specs and code ownership

Each spec page starts with a `Source:` line naming the repository paths it owns (directories, files, or globs; `Source: none` for a cross-cutting page). [`template/docs/AGENTS.md`](template/docs/AGENTS.md#specs) holds the page rules.

The spec tree is recursive. A subsystem is one page, `specs/<name>.md`, until it has parts; then it becomes a node, `specs/<name>/`, holding `architecture.md` and its own `specs/`, the same shape as `docs/` itself. The node's `architecture.md` owns every path of the subsystem and maps its parts; each part's page owns a subset of those paths, and the most specific path wins. A node can split again, and it can move out as the `docs/` of its own repository unchanged. Decisions, tasks, and research stay in the root `docs/`.

```text
docs/
  architecture.md          root map: table of the pages in specs/
  specs/
    reader.md              a subsystem with one page
    cli/                   a subsystem with parts
      architecture.md      Source: every cli path; table of its pages
      specs/
        shot.md            Source: the shot files only
        views.md
```

Agents find the page for a file without searching. `--map` writes a path-to-page table covering every level into the root `AGENTS.md`, which every agent loads at session start; the default check fails when that table is stale. The root `AGENTS.md` limits the cost: an agent reads only the page that owns a file it edits, reads a node's `architecture.md` only before a change that crosses its pages, corrects only the statements its edit made false, and ends its report with a `Docs:` line. One entry file per owned directory names its page in a comment, for agents that start from code; `--pointers` lists pages that no owned file names.

The default check also prints notes, never failures, for pages over about 4,000 words and maps over about 3,000. A page is split when it is that long and its parts own different files; `--split docs/specs/<name>.md` does the mechanical part, moving the page to `specs/<name>/architecture.md`, rewriting the links and pointer comments that name it, and listing other mentions of its file name, and the agent then moves each part onto its own page. Links in the spec tree must name existing headings, so the default check catches a link whose section moved; `--refs <page>` lists every reference to a page by anchor, in code and records too.

Two more queries help a reviewer or coordinator:

```bash
python3 scripts/verify_subsystem_pages.py --owner src/sync/engine.ts
python3 scripts/verify_subsystem_pages.py --changed main
```

`--owner` prints the page that owns a path. `--changed` lists pages whose owned paths differ from the base while the page does not; it exits 0, because an unchanged page can still be correct.

A repository that keeps its pages in another folder, such as `docs/subsystems/`, sets `PAGES` at the top of the script; every node then names its pages folder the same way.

## Check

Kit tests, after changing the initializer or a template:

```bash
python3 -m unittest discover -s tests -v
```

In a target repository:

```bash
python3 scripts/verify_subsystem_pages.py
```

It proves only that the maps, the tree layout, relative links inside the repository, `Source:` paths and their nesting, and the generated `AGENTS.md` table are consistent; it passes with zero pages and does not check whether a page describes its code correctly.

## License

[MIT](LICENSE), Copyright (c) 2026 luwux.

## Changes

- 2026-10-26: after prefill's first split, the check also verifies `#anchors` of links in the spec tree, `--refs` lists references to a page by anchor, `--split` lists mentions of the old file name and leaves finished records' text alone, and the map guide rose to about 3,000 words. `docs/AGENTS.md` says that a dispatcher shared by several parts stays with the node and that a part splits again under the page rule.
- 2026-10-26: specs became a recursive tree. A page can grow into a node (`architecture.md` plus `specs/`) with `--split`; maps carry the page tables, so `docs/specs/README.md` is gone and its rules live in `docs/AGENTS.md`; the check verifies nesting and links and prints word-count notes. Repositories that keep the old script keep the flat layout; adopting the new script means moving the map to `docs/architecture.md` and its index rows into the map.
- 2026-10-13: one layout replaces the `full` and `lite` profiles. Agent Notes, their verifier, the prose and simplification skills, and the `testing.md` template are removed; `product.md`, `decisions/`, `tasks/`, and `research/` take over plans and rationale, and specs live in `docs/specs/`. Installed repositories are migrated by hand.
- 2026-10-13: added specs with `Source:` ownership, the generated `AGENTS.md` table, and `verify_subsystem_pages.py`.
