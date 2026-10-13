# Agent Docs Kit

A documentation layout for repositories that coding agents work in. It gives every fact one home, keeps current-state pages separate from plans and history, and tells an agent which single page to read before it edits a file.

## Layout

| Location | Holds | Changes |
|---|---|---|
| `AGENTS.md` | Standing rules and a generated table from source paths to specs | Table regenerated when a `Source:` line changes |
| `docs/architecture.md` | The map: how subsystems compose and the flows that cross them | With the code |
| `docs/specs/` | One page per subsystem: current behavior and known limitations | With the code, in the same change |
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

The initializer copies only the eight files listed in `init.py` and ignores platform files (`.DS_Store`, `Thumbs.db`, `*.pyc`, `__pycache__/`). It refuses the whole install, writing nothing, when the template holds any other unlisted file, a destination file already exists, or a destination directory is a symlink. For a repository that already has documentation, merge from [`template/`](template/) by hand.

After installing, `docs/architecture.md` and `docs/product.md` state that nothing is recorded yet. Audit the repository and write the architecture map, the product page, and one spec per subsystem before treating the adoption as complete.

## Specs and code ownership

Each spec starts with a `Source:` line naming the repository paths it owns (directories, files, or globs; `Source: none` for a cross-cutting page). [`template/docs/specs/README.md`](template/docs/specs/README.md) holds the page rules.

Agents find the spec for a file without searching. `--map` writes a path-to-spec table into the root `AGENTS.md`, which every agent loads at session start; the default check fails when that table is stale. The root `AGENTS.md` limits the cost: an agent reads only the spec that owns a file it edits, corrects only the statements its edit made false, and ends its report with a `Docs:` line naming those specs. One entry file per owned directory names its spec in a comment, for agents that start from code; `--pointers` lists specs that no owned file names.

Two more queries help a reviewer or coordinator:

```bash
python3 scripts/verify_subsystem_pages.py --owner src/sync/engine.ts
python3 scripts/verify_subsystem_pages.py --changed main
```

`--owner` prints the spec that owns a path. `--changed` lists specs whose owned paths differ from the base while the spec does not; it exits 0, because an unchanged spec can still be correct.

A repository that keeps its pages in another flat directory, such as `docs/subsystems/`, sets `PAGES` at the top of the script instead of renaming the directory. A repository that keeps its architecture map inside that directory lists it in `NON_SUBSYSTEM_PAGES`.

## Check

Kit tests, after changing the initializer or a template:

```bash
python3 -m unittest discover -s tests -v
```

In a target repository:

```bash
python3 scripts/verify_subsystem_pages.py
```

It proves only that the spec index, flat layout, `Source:` paths, and the generated `AGENTS.md` table are consistent; it passes with zero specs and does not check whether a spec describes its code correctly.

## License

[MIT](LICENSE), Copyright (c) 2026 luwux.

## Changes

- 2026-10-13: one layout replaces the `full` and `lite` profiles. Agent Notes, their verifier, the prose and simplification skills, and the `testing.md` template are removed; `product.md`, `decisions/`, `tasks/`, and `research/` take over plans and rationale, and specs live in `docs/specs/`. Installed repositories are migrated by hand.
- 2026-10-13: added specs with `Source:` ownership, the generated `AGENTS.md` table, and `verify_subsystem_pages.py`.
