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
            self.assertIn("created 8 files", installed.stdout)
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
                    "docs/specs/README.md",
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
            self.assertIn("created 10 files", installed.stdout)
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
            self.assertIn("created 8 files", result.stdout)
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
            "src/storage/schema.ts": "schema\n",
            "publish/src/render-page.ts": "render\n",
            "publish/src/cli.ts": "cli\n",
            "app/media/[...key]/route.ts": "route\n",
        }.items():
            (target / path).parent.mkdir(parents=True, exist_ok=True)
            (target / path).write_text(content, encoding="utf-8")
        for command in (
            ("git", "init", "--quiet"),
            ("git", "add", "."),
            (
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
                "fixture",
            ),
        ):
            result = run(*command, cwd=target)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return target

    def write_pages(self, pages: Path, pages_by_name: dict[str, str]) -> None:
        index = pages / "README.md"
        rows = "".join(f"| [{name}]({name}) | {name} |\n" for name in pages_by_name)
        index.write_text(index.read_text(encoding="utf-8") + rows, encoding="utf-8")
        for name, source in pages_by_name.items():
            (pages / name).write_text(f"# {name}\n\nSource: {source}\n\nScope.\n", encoding="utf-8")
        # Keep the generated AGENTS.md table current; structural failures surface in the caller's check.
        self.subsystem_check(pages.parent.parent, "--map")

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
                target / "docs" / "specs",
                {
                    "sync.md": "`src/`",
                    "conflicts.md": "`src/sync/conflict.ts`",
                    "storage.md": "`src/storage/`",
                    "render.md": "`publish/src/render-*.ts`",
                    "privacy.md": "none",
                },
            )
            self.assertEqual(self.subsystem_check(target).returncode, 0)
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

    def test_bracketed_existing_path_is_literal_and_dot_slash_index_links_resolve(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = self.subsystem_repository(temporary)
            pages = target / "docs" / "specs"
            index = pages / "README.md"
            index.write_text(
                index.read_text(encoding="utf-8") + "| [media](./media.md) | media |\n",
                encoding="utf-8",
            )
            (pages / "media.md").write_text(
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
            self.assertEqual(
                result.stdout.strip(), "app/media/[...key]/route.ts -> docs/specs/media.md"
            )

    def test_agents_map_is_generated_and_stale_tables_fail(self) -> None:
        page_root = "docs/specs"
        with tempfile.TemporaryDirectory() as temporary:
            target = self.subsystem_repository(temporary)
            self.write_pages(target / page_root, {"sync.md": "`src/sync/`, `src/storage/schema.ts`"})
            agents = (target / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn(
                f"| `src/sync/`, `src/storage/schema.ts` | [sync]({page_root}/sync.md) |", agents
            )
            self.assertEqual(self.subsystem_check(target).returncode, 0)

            (target / page_root / "sync.md").write_text(
                "# sync.md\n\nSource: `src/sync/`\n", encoding="utf-8"
            )
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
            self.write_pages(
                target / "docs" / "specs",
                {"sync.md": "`src/sync/`", "storage.md": "`src/storage/`"},
            )
            (target / "src" / "sync" / "engine.ts").write_text(
                "// Contract: docs/specs/sync.md\n", encoding="utf-8"
            )
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
            pages = target / "docs" / "specs"
            self.write_pages(
                pages,
                {
                    "sync.md": "`src/sync/`, `src/missing/`, `src/sync/engine.ts/`",
                    "storage.md": "`src/sync/`, `src/*.none`",
                },
            )
            (pages / "orphan.md").write_text("# Orphan\n\nNo source line.\n", encoding="utf-8")
            (pages / "nested").mkdir()
            result = self.subsystem_check(target)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            for expected in (
                "keep docs/specs/ flat",
                "docs/specs/orphan.md — page is missing from README.md",
                "orphan.md:3 — first line after the title must be",
                "src/missing/ does not exist",
                "src/sync/engine.ts/: directories end with `/`, files do not",
                "glob src/*.none matches no file",
                "src/sync/ is declared by both",
            ):
                self.assertIn(expected, result.stderr)

    def test_subsystem_changed_lists_pages_whose_code_moved_alone(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = self.subsystem_repository(temporary)
            pages = target / "docs" / "specs"
            self.write_pages(pages, {"sync.md": "`src/sync/`", "storage.md": "`src/storage/`"})
            for command in (
                ("git", "add", "."),
                (
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
                    "pages",
                ),
            ):
                self.assertEqual(run(*command, cwd=target).returncode, 0)
            (target / "src" / "sync" / "engine.ts").write_text("changed\n", encoding="utf-8")
            (target / "src" / "sync" / "new.ts").write_text("untracked\n", encoding="utf-8")
            (target / "src" / "storage" / "schema.ts").write_text("changed\n", encoding="utf-8")
            with (pages / "storage.md").open("a", encoding="utf-8") as page:
                page.write("Updated with its code.\n")
            result = self.subsystem_check(target, "--changed")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn(
                "docs/specs/sync.md: src/sync/engine.ts, src/sync/new.ts", result.stdout
            )
            self.assertNotIn("docs/specs/storage.md:", result.stdout)

    def test_non_subsystem_pages_setting_exempts_a_map_in_the_pages_folder(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = self.subsystem_repository(temporary)
            pages = target / "docs" / "specs"
            self.write_pages(pages, {"sync.md": "`src/sync/`"})
            (pages / "architecture.md").write_text("# Architecture\n\nThe map.\n", encoding="utf-8")
            rejected = self.subsystem_check(target)
            self.assertEqual(rejected.returncode, 1, rejected.stdout + rejected.stderr)

            script = target / "scripts" / "verify_subsystem_pages.py"
            script.write_text(
                script.read_text(encoding="utf-8").replace(
                    "NON_SUBSYSTEM_PAGES: set[str] = set()",
                    'NON_SUBSYSTEM_PAGES: set[str] = {"architecture.md"}',
                ),
                encoding="utf-8",
            )
            accepted = self.subsystem_check(target)
            self.assertEqual(accepted.returncode, 0, accepted.stdout + accepted.stderr)
            result = self.subsystem_check(target, "--owner", "src/sync/engine.ts")
            self.assertEqual(result.stdout.strip(), "src/sync/engine.ts -> docs/specs/sync.md")


if __name__ == "__main__":
    unittest.main()
