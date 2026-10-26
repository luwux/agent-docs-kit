from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


KIT_ROOT = Path(__file__).resolve().parent.parent
INIT = KIT_ROOT / "init.py"


def run(*args: object, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(arg) for arg in args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


COMMIT = (
    "git",
    "-c",
    "user.name=Docs Kit Test",
    "-c",
    "user.email=docs-kit@example.invalid",
    "-c",
    "commit.gpgsign=false",
    "commit",
    "--quiet",
    "-m",
)


class KitRegressionTests(unittest.TestCase):
    def install(
        self,
        target: Path,
        init: Path = INIT,
        *options: str,
    ) -> subprocess.CompletedProcess[str]:
        result = run(sys.executable, "-B", init, target, "--apply", *options)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def verify(self, target: Path) -> subprocess.CompletedProcess[str]:
        return run(
            sys.executable,
            "-B",
            target / "scripts" / "verify_subsystem_pages.py",
            cwd=target,
        )

    def test_preview_is_read_only_and_apply_copies_only_reviewed_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "target"
            target.mkdir()

            preview = run(sys.executable, "-B", INIT, target)
            self.assertEqual(preview.returncode, 0, preview.stdout + preview.stderr)
            self.assertIn("preview only", preview.stdout)
            self.assertNotIn(".DS_Store", preview.stdout)
            self.assertEqual(list(target.iterdir()), [])

            installed = self.install(target)
            self.assertIn("created 7 files", installed.stdout)
            self.assertEqual(
                sorted(
                    path.relative_to(target).as_posix()
                    for path in target.rglob("*")
                    if path.is_file()
                ),
                [
                    "AGENTS.md",
                    "docs/AGENTS.md",
                    "docs/architecture.md",
                    "docs/decisions/TEMPLATE.md",
                    "docs/product.md",
                    "docs/tasks/TEMPLATE.md",
                    "scripts/verify_subsystem_pages.py",
                ],
            )
            verified = self.verify(target)
            self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)

    def test_claude_symlinks_point_at_sibling_agents_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "target"
            target.mkdir()

            installed = self.install(target, INIT, "--claude-symlinks")
            self.assertIn("created 9 files", installed.stdout)
            for link in ("CLAUDE.md", "docs/CLAUDE.md"):
                self.assertEqual(os.readlink(target / link), "AGENTS.md", link)
                self.assertTrue((target / link).is_file(), link)

    def test_unreviewed_template_file_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied_kit = Path(temporary) / "kit"
            shutil.copytree(KIT_ROOT, copied_kit)
            (copied_kit / "template" / "unreviewed.md").write_text(
                "unreviewed\n",
                encoding="utf-8",
            )
            target = Path(temporary) / "target"
            target.mkdir()

            result = run(sys.executable, "-B", copied_kit / "init.py", target)
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("unexpected template file: unreviewed.md", result.stderr)
            self.assertEqual(list(target.iterdir()), [])

    def test_finder_metadata_is_ignored_not_installed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied_kit = Path(temporary) / "kit"
            shutil.copytree(KIT_ROOT, copied_kit)
            template = copied_kit / "template"
            junk = (
                template / "docs" / ".DS_Store",
                template / "docs" / "Thumbs.db",
                template / "scripts" / "stray.pyc",
                template / "scripts" / "__pycache__" / "verify_subsystem_pages.cpython-39.pyc",
                template / "scripts" / "__pycache__" / "notes.txt",
            )
            for path in junk:
                path.parent.mkdir(exist_ok=True)
                path.write_bytes(b"metadata")
            target = Path(temporary) / "target"
            target.mkdir()

            result = self.install(target, copied_kit / "init.py")
            self.assertIn("created 7 files", result.stdout)
            for path in junk:
                relative = path.relative_to(template)
                self.assertNotIn(relative.name, result.stdout)
                self.assertFalse((target / relative).exists(), relative)
            self.assertFalse((target / "scripts" / "__pycache__").exists())

            template_metadata = template / "docs" / ".DS_Store"
            template_metadata.unlink()
            template_metadata.symlink_to("AGENTS.md")
            second_target = Path(temporary) / "second-target"
            second_target.mkdir()
            unsafe_template = run(
                sys.executable,
                "-B",
                copied_kit / "init.py",
                second_target,
            )
            self.assertEqual(
                unsafe_template.returncode,
                2,
                unsafe_template.stdout + unsafe_template.stderr,
            )
            self.assertIn("unexpected template file: docs/.DS_Store", unsafe_template.stderr)

    def test_template_markdown_links_resolve(self) -> None:
        link = re.compile(r"\]\(([^)#:]+)(?:#[^)]*)?\)")
        for document in (KIT_ROOT / "template").rglob("*.md"):
            # Inline code holds illustrative link syntax, not real references.
            prose = re.sub(r"`[^`]*`", "", document.read_text(encoding="utf-8"))
            for target in link.findall(prose):
                resolved = (document.parent / target).resolve()
                self.assertTrue(resolved.exists(), f"{document}: {target}")

    def test_collision_preflight_is_globally_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "target"
            existing = target / "docs" / "architecture.md"
            existing.parent.mkdir(parents=True)
            existing.write_text("owned by target\n", encoding="utf-8")

            result = run(sys.executable, "-B", INIT, target, "--apply")
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("existing destinations", result.stderr)
            self.assertEqual(existing.read_text(encoding="utf-8"), "owned by target\n")
            self.assertFalse((target / "AGENTS.md").exists())
            self.assertFalse((target / "scripts").exists())

    def test_destination_directory_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "target"
            external = Path(temporary) / "external"
            target.mkdir()
            external.mkdir()
            (target / "docs").symlink_to(external, target_is_directory=True)

            result = run(sys.executable, "-B", INIT, target, "--apply")
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("existing directory path is a symlink", result.stderr)
            self.assertEqual(list(external.iterdir()), [])
            self.assertFalse((target / "AGENTS.md").exists())

    def subsystem_repository(self, temporary: str) -> Path:
        target = Path(temporary) / "target"
        target.mkdir()
        self.install(target)
        for path, content in {
            "src/sync/engine.ts": "engine\n",
            "src/sync/conflict.ts": "conflict\n",
            "src/sync/transport/socket.ts": "socket\n",
            "src/storage/schema.ts": "schema\n",
            "publish/src/render-page.ts": "render\n",
            "publish/src/cli.ts": "cli\n",
            "app/media/[...key]/route.ts": "route\n",
        }.items():
            (target / path).parent.mkdir(parents=True, exist_ok=True)
            (target / path).write_text(content, encoding="utf-8")
        for command in (("git", "init", "--quiet"), ("git", "add", "."), COMMIT + ("fixture",)):
            result = run(*command, cwd=target)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return target

    def write_pages(self, node_map: Path, pages_by_name: dict[str, str], regenerate: bool = True) -> None:
        """Add pages to the node whose map is node_map; a name ending in `/` becomes a node."""

        pages = node_map.parent / "specs"
        pages.mkdir(exist_ok=True)
        rows = ""
        for name, source in pages_by_name.items():
            if name.endswith("/"):
                path = pages / name / "architecture.md"
                path.parent.mkdir()
                rows += f"| [{name[:-1]}](specs/{name}architecture.md) | part |\n"
            else:
                path = pages / name
                rows += f"| [{name}](specs/{name}) | part |\n"
            path.write_text(f"# {name}\n\nSource: {source}\n\nScope.\n", encoding="utf-8")
        node_map.write_text(node_map.read_text(encoding="utf-8") + rows, encoding="utf-8")
        if regenerate:
            # Keep the generated AGENTS.md table current; structural failures surface in the caller's check.
            self.subsystem_check(self.repository_of(node_map), "--map")

    def repository_of(self, path: Path) -> Path:
        while not (path / "AGENTS.md").is_file() or not (path / "scripts").is_dir():
            path = path.parent
        return path

    def subsystem_check(self, target: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return run(
            sys.executable,
            "-B",
            target / "scripts" / "verify_subsystem_pages.py",
            *args,
            cwd=target,
        )

    def test_subsystem_verifier_accepts_fresh_install(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = self.subsystem_repository(temporary)
            result = self.subsystem_check(target)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("0 owning page(s)", result.stdout)

    def test_subsystem_owner_prefers_file_then_glob_then_deeper_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = self.subsystem_repository(temporary)
            self.write_pages(
                target / "docs" / "architecture.md",
                {
                    "sync.md": "`src/`",
                    "conflicts.md": "`src/sync/conflict.ts`",
                    "storage.md": "`src/storage/`",
                    "render.md": "`publish/src/render-*.ts`",
                    "privacy.md": "none",
                },
            )
            checked = self.subsystem_check(target)
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
            result = self.subsystem_check(
                target,
                "--owner",
                "src/sync/engine.ts",
                "src/sync/conflict.ts",
                str(target / "src" / "storage" / "schema.ts"),
                "publish/src/render-page.ts",
                "publish/src/cli.ts",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(
                result.stdout.splitlines(),
                [
                    "src/sync/engine.ts -> docs/specs/sync.md",
                    "src/sync/conflict.ts -> docs/specs/conflicts.md",
                    "src/storage/schema.ts -> docs/specs/storage.md",
                    "publish/src/render-page.ts -> docs/specs/render.md",
                    "publish/src/cli.ts -> (no subsystem page)",
                ],
            )

    def test_nested_node_owns_leftovers_and_its_pages_own_their_parts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = self.subsystem_repository(temporary)
            self.write_pages(target / "docs" / "architecture.md", {"sync/": "`src/sync/`"}, regenerate=False)
            node = target / "docs" / "specs" / "sync"
            self.write_pages(node / "architecture.md", {"conflicts.md": "`src/sync/conflict.ts`"}, regenerate=False)
            self.write_pages(node / "architecture.md", {"transport/": "`src/sync/transport/`"}, regenerate=False)
            self.write_pages(
                node / "specs" / "transport" / "architecture.md", {"socket.md": "`src/sync/transport/socket.ts`"}
            )
            checked = self.subsystem_check(target)
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
            self.assertIn("2 of them node(s)", checked.stdout)
            owners = self.subsystem_check(
                target, "--owner", "src/sync/engine.ts", "src/sync/conflict.ts", "src/sync/transport/socket.ts"
            )
            self.assertEqual(
                owners.stdout.splitlines(),
                [
                    "src/sync/engine.ts -> docs/specs/sync/architecture.md",
                    "src/sync/conflict.ts -> docs/specs/sync/specs/conflicts.md",
                    "src/sync/transport/socket.ts -> docs/specs/sync/specs/transport/specs/socket.md",
                ],
            )
            agents = (target / "AGENTS.md").read_text(encoding="utf-8")
            for row in (
                "| `src/sync/` | [sync](docs/specs/sync/architecture.md) |",
                "| `src/sync/conflict.ts` | [sync/conflicts](docs/specs/sync/specs/conflicts.md) |",
                "| `src/sync/transport/` | [sync/transport](docs/specs/sync/specs/transport/architecture.md) |",
                "| `src/sync/transport/socket.ts` | [sync/transport/socket](docs/specs/sync/specs/transport/specs/socket.md) |",
            ):
                self.assertIn(row, agents)

    def test_nested_node_rejects_paths_outside_it_and_incomplete_folders(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = self.subsystem_repository(temporary)
            self.write_pages(
                target / "docs" / "architecture.md",
                {"sync/": "`src/sync/`", "empty/": "`src/storage/`", "bare/": "none"},
                regenerate=False,
            )
            specs = target / "docs" / "specs"
            self.write_pages(specs / "sync" / "architecture.md", {"render.md": "`publish/src/render-page.ts`"}, regenerate=False)
            (specs / "sync" / "tasks").mkdir()
            (specs / "empty" / "specs").mkdir()
            (specs / "sync" / "specs" / "unlisted.md").write_text(
                "# Unlisted\n\nSource: `src/sync/engine.ts`\n", encoding="utf-8"
            )
            result = self.subsystem_check(target)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            for expected in (
                "docs/specs/sync/specs/render.md declares paths outside its node docs/specs/sync/architecture.md: publish/src/render-page.ts",
                "docs/specs/sync/tasks — a node holds only architecture.md and specs/",
                "docs/specs/empty/specs/ — the node has no pages",
                "docs/specs/bare/specs/ — a node needs a specs/ folder",
                "docs/specs/sync/specs/unlisted.md — page is missing from the table in docs/specs/sync/architecture.md",
            ):
                self.assertIn(expected, result.stderr)

    def test_legacy_index_and_map_inside_the_pages_folder_are_named(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = self.subsystem_repository(temporary)
            specs = target / "docs" / "specs"
            specs.mkdir()
            (specs / "README.md").write_text("# Specs\n", encoding="utf-8")
            (specs / "architecture.md").write_text("# Architecture\n", encoding="utf-8")
            result = self.subsystem_check(target)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("docs/specs/README.md — the index lives in docs/architecture.md", result.stderr)
            self.assertIn("docs/specs/architecture.md — move the root map to docs/architecture.md", result.stderr)

    def test_bracketed_existing_path_is_literal_and_dot_slash_map_links_resolve(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = self.subsystem_repository(temporary)
            root = target / "docs" / "architecture.md"
            root.write_text(root.read_text(encoding="utf-8") + "| [media](./specs/media.md) | media |\n", encoding="utf-8")
            (target / "docs" / "specs").mkdir()
            (target / "docs" / "specs" / "media.md").write_text(
                "# Media\n\nSource: `app/media/[...key]/`\n", encoding="utf-8"
            )
            self.subsystem_check(target, "--map")
            self.assertIn(
                "| `app/media/[...key]/` | [media](docs/specs/media.md) |",
                (target / "AGENTS.md").read_text(encoding="utf-8"),
            )
            checked = self.subsystem_check(target)
            self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
            result = self.subsystem_check(target, "--owner", "app/media/[...key]/route.ts")
            self.assertEqual(result.stdout.strip(), "app/media/[...key]/route.ts -> docs/specs/media.md")

    def test_agents_map_is_generated_and_stale_tables_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = self.subsystem_repository(temporary)
            self.write_pages(target / "docs" / "architecture.md", {"sync.md": "`src/sync/`, `src/storage/schema.ts`"})
            agents = (target / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("| `src/sync/`, `src/storage/schema.ts` | [sync](docs/specs/sync.md) |", agents)
            self.assertEqual(self.subsystem_check(target).returncode, 0)

            (target / "docs" / "specs" / "sync.md").write_text("# sync.md\n\nSource: `src/sync/`\n", encoding="utf-8")
            stale = self.subsystem_check(target)
            self.assertEqual(stale.returncode, 1, stale.stdout + stale.stderr)
            self.assertIn("subsystem table is stale", stale.stderr)
            rewritten = self.subsystem_check(target, "--map")
            self.assertIn("updated the subsystem table", rewritten.stdout)
            self.assertEqual(self.subsystem_check(target).returncode, 0)

            # A formatter that pads cells and widens the separator keeps the table current.
            agents_path = target / "AGENTS.md"
            aligned = agents_path.read_text(encoding="utf-8").replace(
                "|---|---|", "| ------------- | ------------------------------- |"
            ).replace("| `src/sync/` |", "| `src/sync/`   |")
            agents_path.write_text(aligned, encoding="utf-8")
            formatted = self.subsystem_check(target)
            self.assertEqual(formatted.returncode, 0, formatted.stdout + formatted.stderr)

    def test_pointers_lists_pages_no_owned_file_names(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = self.subsystem_repository(temporary)
            self.write_pages(target / "docs" / "architecture.md", {"sync.md": "`src/sync/`", "storage.md": "`src/storage/`"})
            (target / "src" / "sync" / "engine.ts").write_text("// Spec: docs/specs/sync.md\n", encoding="utf-8")
            # A README link inside owned paths is not a pointer for agents that start from code.
            (target / "src" / "storage" / "README.md").write_text(
                "See [storage](../../docs/specs/storage.md).\n", encoding="utf-8"
            )
            result = self.subsystem_check(target, "--pointers")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("docs/specs/storage.md", result.stdout)
            self.assertNotIn("docs/specs/sync.md", result.stdout)

    def test_subsystem_verifier_rejects_inconsistent_pages(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = self.subsystem_repository(temporary)
            self.write_pages(
                target / "docs" / "architecture.md",
                {
                    "sync.md": "`src/sync/`, `src/missing/`, `src/sync/engine.ts/`",
                    "storage.md": "`src/sync/`, `src/*.none`",
                },
            )
            specs = target / "docs" / "specs"
            (specs / "orphan.md").write_text("# Orphan\n\nNo source line. See [gone](gone.md).\n", encoding="utf-8")
            (specs / "notes.txt").write_text("stray\n", encoding="utf-8")
            result = self.subsystem_check(target)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            for expected in (
                "docs/specs/notes.txt — only Markdown pages and node folders are allowed",
                "docs/specs/orphan.md — page is missing from the table in docs/architecture.md",
                "orphan.md:3 — first line after the title must be",
                "docs/specs/orphan.md:3 — gone.md does not exist",
                "src/missing/ does not exist",
                "src/sync/engine.ts/: directories end with `/`, files do not",
                "glob src/*.none matches no file",
                "src/sync/ is declared by both",
            ):
                self.assertIn(expected, result.stderr)

    def test_subsystem_changed_lists_pages_whose_code_moved_alone(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = self.subsystem_repository(temporary)
            self.write_pages(target / "docs" / "architecture.md", {"sync.md": "`src/sync/`", "storage.md": "`src/storage/`"})
            for command in (("git", "add", "."), COMMIT + ("pages",)):
                self.assertEqual(run(*command, cwd=target).returncode, 0)
            (target / "src" / "sync" / "engine.ts").write_text("changed\n", encoding="utf-8")
            (target / "src" / "sync" / "new.ts").write_text("untracked\n", encoding="utf-8")
            (target / "src" / "storage" / "schema.ts").write_text("changed\n", encoding="utf-8")
            with (target / "docs" / "specs" / "storage.md").open("a", encoding="utf-8") as page:
                page.write("Updated with its code.\n")
            result = self.subsystem_check(target, "--changed")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("docs/specs/sync.md: src/sync/engine.ts, src/sync/new.ts", result.stdout)
            self.assertNotIn("docs/specs/storage.md:", result.stdout)

    def test_split_turns_a_page_into_a_node_and_rewrites_references(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = self.subsystem_repository(temporary)
            self.write_pages(target / "docs" / "architecture.md", {"sync.md": "`src/sync/`", "storage.md": "`src/storage/`"})
            specs = target / "docs" / "specs"
            (specs / "sync.md").write_text(
                "# Sync\n\nSource: `src/sync/`\n\nStores via [storage](storage.md#schema); "
                "code in [engine](../../src/sync/engine.ts); see [below](#retries) and `[not a link](x.md)`.\n\n"
                "## Retries\n\nBacks off.\n",
                encoding="utf-8",
            )
            (specs / "storage.md").write_text(
                "# Storage\n\nSource: `src/storage/`\n\nSynced by [sync](sync.md#retries).\n\n## Schema\n",
                encoding="utf-8",
            )
            (target / "src" / "sync" / "engine.ts").write_text("// Spec: docs/specs/sync.md\n", encoding="utf-8")
            (target / "src" / "sync" / "conflict.ts").write_text(
                "// Spec: docs/specs/sync.md#retries\n", encoding="utf-8"
            )
            (target / "src" / "checks.ts").write_text('export const owner = "sync.md#retries";\n', encoding="utf-8")
            (target / "src" / "sync" / "transport" / "socket.ts").write_text(
                "// Retries follow docs/specs/sync.md#retries.\n", encoding="utf-8"
            )
            (target / "docs" / "notes.md").write_text("Mentions `docs/specs/sync.md` in prose.\n", encoding="utf-8")
            tasks = target / "docs" / "tasks"
            (tasks / "0001-done.md").write_text(
                "# 0001: Done\n\n- Status: Done\n\nEdited `docs/specs/sync.md`.\n", encoding="utf-8"
            )
            (tasks / "0002-open.md").write_text(
                "# 0002: Open\n\n- Status: Open\n\nWill edit `docs/specs/sync.md`.\n", encoding="utf-8"
            )
            self.assertEqual(self.subsystem_check(target).returncode, 0)

            split = self.subsystem_check(target, "--split", "docs/specs/sync.md")
            self.assertEqual(split.returncode, 0, split.stdout + split.stderr)
            self.assertIn("moved docs/specs/sync.md -> docs/specs/sync/architecture.md", split.stdout)
            self.assertIn("    docs/notes.md:1\n", split.stdout)
            self.assertIn("    src/checks.ts:1\n", split.stdout)
            self.assertIn("    docs/tasks/0002-open.md:5\n", split.stdout)
            self.assertIn("leave mentions in finished records as written: docs/tasks/0001-done.md:5", split.stdout)
            moved = (specs / "sync" / "architecture.md").read_text(encoding="utf-8")
            self.assertIn("[storage](../storage.md#schema)", moved)
            self.assertIn("[engine](../../../src/sync/engine.ts)", moved)
            self.assertIn("[below](#retries)", moved)
            self.assertIn("`[not a link](x.md)`", moved)
            self.assertIn("[sync](sync/architecture.md#retries)", (specs / "storage.md").read_text(encoding="utf-8"))
            self.assertIn(
                "(specs/sync/architecture.md)", (target / "docs" / "architecture.md").read_text(encoding="utf-8")
            )
            self.assertEqual(
                (target / "src" / "sync" / "engine.ts").read_text(encoding="utf-8"),
                "// Spec: docs/specs/sync/architecture.md\n",
            )
            self.assertTrue((specs / "sync" / "specs").is_dir())

            unfinished = self.subsystem_check(target)
            self.assertEqual(unfinished.returncode, 1, unfinished.stdout + unfinished.stderr)
            self.assertIn("the node has no pages", unfinished.stderr)

            # Move the Retries section onto a part page; links to its old anchor now break.
            node_map = specs / "sync" / "architecture.md"
            node_map.write_text(moved.split("## Retries")[0], encoding="utf-8")
            self.write_pages(node_map, {"conflicts.md": "`src/sync/conflict.ts`"})
            broken = self.subsystem_check(target)
            self.assertEqual(broken.returncode, 1, broken.stdout + broken.stderr)
            self.assertIn(
                "docs/specs/storage.md:5 — sync/architecture.md#retries: docs/specs/sync/architecture.md "
                "has no heading for #retries",
                broken.stderr,
            )
            refs = self.subsystem_check(target, "--refs", "docs/specs/sync/architecture.md")
            self.assertEqual(refs.returncode, 0, refs.stdout + refs.stderr)
            retries = next(line for line in refs.stdout.splitlines() if line.startswith("  #retries"))
            self.assertIn("no such heading", retries)
            for place in (
                "docs/specs/storage.md:5",
                "docs/specs/sync/architecture.md:5",
                "src/sync/conflict.ts:1",
                "src/sync/transport/socket.ts:1",
            ):
                self.assertIn(place, retries)
            self.assertNotIn("#retries.", refs.stdout)
            plain = next(line for line in refs.stdout.splitlines() if line.startswith("  (no anchor)"))
            for place in ("AGENTS.md:", "docs/architecture.md:", "src/sync/engine.ts:1"):
                self.assertIn(place, plain)

            for path in (specs / "storage.md", node_map):
                path.write_text(
                    path.read_text(encoding="utf-8").replace("sync/architecture.md#retries", "sync/specs/conflicts.md")
                    .replace("(#retries)", "(specs/conflicts.md)"),
                    encoding="utf-8",
                )
            # --map refuses while the tree has errors, so regenerate once the links are fixed.
            self.assertEqual(self.subsystem_check(target, "--map").returncode, 0)
            finished = self.subsystem_check(target)
            self.assertEqual(finished.returncode, 0, finished.stdout + finished.stderr)

    def test_links_must_name_existing_headings(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = self.subsystem_repository(temporary)
            self.write_pages(target / "docs" / "architecture.md", {"query.md": "`src/sync/`", "store.md": "`src/storage/`"})
            specs = target / "docs" / "specs"
            (specs / "query.md").write_text(
                "# Query\n\nSource: `src/sync/`\n\n"
                '### `chist search "<q>" [--fts | --semantic]`\n\n'
                "## 同步与冲突\n\n## Notes\n\n## Notes\n\n<a id=\"legacy\"></a>\n\n"
                "```\n## Not a heading\n```\n",
                encoding="utf-8",
            )
            links = [
                'query.md#chist-search-q---fts----semantic',
                "query.md#同步与冲突",
                "query.md#%E5%90%8C%E6%AD%A5%E4%B8%8E%E5%86%B2%E7%AA%81",
                "query.md#notes-1",
                "query.md#legacy",
                "../../src/sync/engine.ts#L1",
            ]
            (specs / "store.md").write_text(
                "# Store\n\nSource: `src/storage/`\n\n" + "".join(f"[x]({link}) " for link in links) + "\n",
                encoding="utf-8",
            )
            passed = self.subsystem_check(target)
            self.assertEqual(passed.returncode, 0, passed.stdout + passed.stderr)

            with (specs / "store.md").open("a", encoding="utf-8") as page:
                page.write("[x](query.md#not-a-heading) [y](#nowhere)\n")
            failed = self.subsystem_check(target)
            self.assertEqual(failed.returncode, 1, failed.stdout + failed.stderr)
            self.assertIn("query.md#not-a-heading: docs/specs/query.md has no heading for #not-a-heading", failed.stderr)
            self.assertIn("#nowhere: docs/specs/store.md has no heading for #nowhere", failed.stderr)

    def test_long_pages_and_maps_get_notes_without_failing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = self.subsystem_repository(temporary)
            self.write_pages(target / "docs" / "architecture.md", {"sync.md": "`src/sync/`", "storage.md": "`src/storage/`"})
            with (target / "docs" / "specs" / "sync.md").open("a", encoding="utf-8") as page:
                page.write("word " * 4100 + "\n")
            with (target / "docs" / "specs" / "storage.md").open("a", encoding="utf-8") as page:
                page.write("字" * 3000 + "\n")
            result = self.subsystem_check(target)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("note: docs/specs/sync.md has", result.stdout)
            self.assertNotIn("note: docs/specs/storage.md", result.stdout)


if __name__ == "__main__":
    unittest.main()
