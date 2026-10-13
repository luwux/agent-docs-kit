# Subsystems

One reference page per subsystem: the source paths it owns, the data it moves, its behavior, failures, configuration, and extension points. [architecture.md](../architecture.md) is the map across subsystems and links each one here.

## Page rules

- Keep this folder flat: one Markdown page per subsystem, named for the subsystem in kebab-case. When a page covers more than one subsystem, split it into sibling pages; do not nest folders.
- The first line after the title is `Source:` followed by the backticked repository paths the page owns, for example ``Source: `src/sync/`, `src/storage/schema.ts`, `publish/src/render-*.ts` ``. A directory path ends with `/`; in a glob, `*` stays within one path segment and `**` crosses segments. A path that exists on disk is literal even when it contains `[`, `*`, or `?`, such as `app/media/[...key]/`. Each declared path belongs to one page. A more specific declaration on another page takes precedence: a file over a glob, a glob over a directory, and a deeper directory over its parent.
- A cross-cutting page that owns no code, such as privacy or configuration rules that span subsystems, writes `Source: none`. Prefer an owning page; a shared file still belongs to one page, and the other pages link it.
- Open with one scope paragraph: what the subsystem owns, which subsystems it calls or is called by (linked), and what it does not own.
- Then document what applies: data and types, behavior and lifecycle, failure and recovery, configuration, and extension points. Link the authoritative code instead of restating it.
- Cross-subsystem flows belong in [architecture.md](../architecture.md) or a topic document it links; decision rationale belongs in [Agent Notes](../../.agents/notes/README.md).
- One entry file of each owned directory, such as the package comment, the main type, or the `index` module, carries one comment line naming the page, for example `// Contract: docs/subsystems/sync.md`. Files that cannot hold comments, such as JSON, need none.
- `python3 scripts/verify_subsystem_pages.py` checks this folder and the generated table in the root `AGENTS.md`; `--map` regenerates that table after a `Source:` line changes. `--owner <path>` names the page for a code path, `--changed [BASE]` lists pages whose owned paths changed while the page did not, and `--pointers` lists pages that no owned file names.

## Index

| Page | Owns |
|---|---|
