# DSH Agent Docs Kit

**This kit is modeled on the agent documentation system of [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) (DSH).** It extracts the project-independent parts — standing agent instructions, one home per fact, current-state docs, decision records, and the prose and simplification skills — into a scaffold you can install into any repository. It is not affiliated with or endorsed by DeepSeek.

## Profiles

| | `full` (default) | `lite` |
|---|---|---|
| For | Projects that keep a long-lived decision record with a format check | Small projects, one person working with agents, new repositories |
| Documents | `docs/architecture.md`, `docs/testing.md`, and `.agents/notes/` with the proposed / implemented / rejected / archived lifecycle | `docs/specs/` (current state), `docs/decisions/` (ADRs), `docs/tasks/` (task briefs) |
| When to write a record | An Agent Note only for durable decision rationale that code, tests, and docs cannot carry | An ADR only when a future agent would likely reverse the decision; a task brief only for work that spans sessions |
| Size budgets | None | Task brief about 60 lines including its result; ADR about 50 lines |
| Check | `scripts/verify_agent_notes.py` (structure and format only) | None |
| Skills | Full prose and simplification skills | Condensed skills without Agent Notes |
| Files installed | 12 | 8 |

Both profiles keep the one-home-per-fact rule and the current-state rule for specs.

## Install

Requires Python 3.9 or later. Preview first; nothing is written:

```bash
python3 init.py /absolute/path/to/project --profile lite
```

Then apply:

```bash
python3 init.py /absolute/path/to/project --profile lite --apply
```

Omit `--profile` for `full`. Add `--claude-symlinks` to also create `CLAUDE.md -> AGENTS.md` links.

The initializer copies only the files each profile lists in `init.py` and ignores platform files (`.DS_Store`, `Thumbs.db`, `*.pyc`, `__pycache__/`). It refuses the whole install, writing nothing, when the template holds any other unlisted file, a destination file already exists, or a destination directory is a symlink. For a repository that already has documentation, merge from [`template/`](template/) or [`template-lite/`](template-lite/) by hand.

After installing, the architecture document states that the target's architecture is not yet recorded. Audit the repository and record its current facts before treating the adoption as complete.

## Check

Kit tests, after changing the initializer or a template:

```bash
python3 -m unittest discover -s tests -v
```

In a `full` target repository:

```bash
python3 scripts/verify_agent_notes.py
```

The verifier proves only that Agent Note directories, filenames, headers, statuses, and required sections are consistent; it passes with zero notes and does not check links, supersession, or whether content is true.

## Origin and license

The template text is adapted from DeepSeek Harness, pinned at commit [`b150a55`](https://github.com/deepseek-ai/deepseek-harness/tree/b150a551b8d465e31e418e1b2eaf5e79bbb7d28e) and last reviewed at [`21638c5`](https://github.com/deepseek-ai/deepseek-harness/tree/21638c56315ae6a2b552d6091945d3144c9af32e). Product-specific architecture, commands, release flow, and bilingual machinery were removed. [UPSTREAM.md](UPSTREAM.md) (in Chinese) maps each mechanism to its upstream source and lists every local deviation.

- DSH-derived text remains under the [DeepSeek Harness MIT license](template/.agents/LICENSE.deepseek-harness), Copyright (c) 2026 DeepSeek. Both templates install a copy of that notice as `.agents/LICENSE.deepseek-harness`; keep it in target repositories.
- Everything else in this repository is under the [MIT license](LICENSE), Copyright (c) 2026 luwux.

## Changes

- 2026-09-27: `full` synced with DSH `21638c5`: Agent Notes only for durable rationale, notes that record only small UI or mechanical changes are deleted, and the simplification skill is rewritten around removable obligations. Installed repositories must be updated by hand.
- 2026-09-27: added the `lite` profile (`template-lite/`, `--profile`); the initializer ignores `.DS_Store`, `Thumbs.db`, `*.pyc`, and `__pycache__/` instead of aborting on anything but `.DS_Store`.
