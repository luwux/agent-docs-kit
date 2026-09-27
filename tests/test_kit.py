from __future__ import annotations

from pathlib import Path
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
            target / "scripts" / "verify_agent_notes.py",
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
            self.assertIn("created 12 files", installed.stdout)
            self.assertEqual(
                [path for path in target.rglob(".DS_Store")],
                [],
            )
            verified = self.verify(target)
            self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)

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
            (copied_kit / "template" / "docs" / ".DS_Store").write_bytes(b"metadata")
            target = Path(temporary) / "target"
            target.mkdir()

            result = self.install(target, copied_kit / "init.py")
            self.assertNotIn(".DS_Store", result.stdout)
            self.assertFalse((target / "docs" / ".DS_Store").exists())
            (target / ".agents" / "notes" / ".DS_Store").write_bytes(b"metadata")
            verified = self.verify(target)
            self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)

            metadata = target / ".agents" / "notes" / ".DS_Store"
            metadata.unlink()
            metadata.symlink_to("README.md")
            rejected = self.verify(target)
            self.assertEqual(rejected.returncode, 1, rejected.stdout + rejected.stderr)
            self.assertIn("unexpected Agent Note root entry", rejected.stderr)

            template_metadata = copied_kit / "template" / "docs" / ".DS_Store"
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
            self.assertFalse((target / ".agents").exists())

    def test_destination_directory_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "target"
            external = Path(temporary) / "external"
            target.mkdir()
            external.mkdir()
            (target / ".agents").symlink_to(external, target_is_directory=True)

            result = run(sys.executable, "-B", INIT, target, "--apply")
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("existing directory path is a symlink", result.stderr)
            self.assertEqual(list(external.iterdir()), [])
            self.assertFalse((target / "AGENTS.md").exists())

    def test_claude_link_must_target_exact_agents_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "target"
            target.mkdir()
            self.install(target, INIT, "--claude-symlinks")

            verified = self.verify(target)
            self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)

            link = target / ".agents" / "notes" / "implemented" / "CLAUDE.md"
            link.unlink()
            link.symlink_to("../../README.md")
            rejected = self.verify(target)
            self.assertEqual(rejected.returncode, 1, rejected.stdout + rejected.stderr)
            self.assertIn(
                "CLAUDE.md must target exactly AGENTS.md",
                rejected.stderr,
            )

            link.unlink()
            link.symlink_to("AGENTS.md")
            proposed = target / ".agents" / "notes" / "proposed"
            proposed.mkdir()
            (proposed / "CLAUDE.md").symlink_to("AGENTS.md")
            dangling = self.verify(target)
            self.assertEqual(dangling.returncode, 1, dangling.stdout + dangling.stderr)
            self.assertIn(
                "CLAUDE.md requires a sibling regular AGENTS.md",
                dangling.stderr,
            )

    def test_verifier_rejects_impossible_filename_date(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "target"
            target.mkdir()
            self.install(target)
            note_directory = target / ".agents" / "notes" / "proposed" / "process"
            note_directory.mkdir(parents=True)
            (note_directory / "2026-02-30-invalid-date.md").write_text(
                """# Agent Note: Invalid date

Status: proposed

## Problem

The filename date is impossible.

## Proposal

Reject it.

## Alternatives considered

**Keep it.** It would make ordering unreliable.

## Acceptance criteria

The verifier rejects the file.

## Risks

None.
""",
                encoding="utf-8",
            )

            verified = self.verify(target)
            self.assertEqual(verified.returncode, 1, verified.stdout + verified.stderr)
            self.assertIn("filename date is not a real calendar date", verified.stderr)

    def test_verifier_accepts_each_lifecycle_with_on_demand_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "target"
            target.mkdir()
            self.install(target)
            notes = target / ".agents" / "notes"
            fixtures = {
                notes / "proposed" / "process" / "2026-08-29-proposal.md": """# Agent Note: Proposal

Status: proposed

## Problem

A process decision is needed.

## Proposal

Adopt the process.

## Alternatives considered

**Keep the old process.** It does not meet the requirement.

## Acceptance criteria

The new process is observable.

## Risks

The process adds one rule.
""",
                notes / "implemented" / "architecture" / "2026-08-29-decision.md": """# Agent Note: Decision

Status: implemented

## Problem

The architecture needs one owner.

## Decision

The architecture document owns the current map.

## Alternatives considered

**Duplicate the map.** Duplicate owners drift.

## Consequences

Readers follow one link and maintain one map.
""",
                notes / "rejected" / "feature" / "2026-08-29-rejection.md": """# Agent Note: Rejection

Status: rejected — the feature has no production consumer

## Problem

The proposal adds unused behavior.

## Proposal

Add the behavior.

## Alternatives considered

**Wait for a consumer.** This avoids speculative code.
""",
                notes / "archived" / "testing" / "2026-08-29-archive.md": """# Agent Note: Archive

Status: implemented
Archived: 2026-08-29

## Problem

The completed test decision no longer guides current work.

## Decision

The focused fixture records the decision.

## Alternatives considered

**Keep it active.** It has no remaining maintenance value.

## Consequences

The frozen record remains available as history.
""",
            }
            for path, content in fixtures.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")

            verified = self.verify(target)
            self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)
            self.assertIn("3 active and 1 archived", verified.stdout)

    def test_archived_note_keeps_implemented_section_skeleton(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "target"
            target.mkdir()
            self.install(target)
            note_directory = target / ".agents" / "notes" / "archived" / "process"
            note_directory.mkdir()
            (note_directory / "2026-08-29-empty-archive.md").write_text(
                """# Agent Note: Empty archive

Status: implemented
Archived: 2026-08-29

""",
                encoding="utf-8",
            )

            verified = self.verify(target)
            self.assertEqual(verified.returncode, 1, verified.stdout + verified.stderr)
            self.assertIn("missing the required `## Decision` section", verified.stderr)
            self.assertIn("missing `## Alternatives considered`", verified.stderr)

    @unittest.skipIf(shutil.which("git") is None, "git is required")
    def test_fresh_clone_preserves_a_valid_empty_note_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary) / "repository"
            clone = Path(temporary) / "clone"
            repository.mkdir()
            self.install(repository)

            commands = (
                ("git", "init", "--quiet", repository),
                ("git", "-C", repository, "add", "."),
                (
                    "git",
                    "-C",
                    repository,
                    "-c",
                    "user.name=Docs Kit Test",
                    "-c",
                    "user.email=docs-kit@example.invalid",
                    "-c",
                    "commit.gpgsign=false",
                    "commit",
                    "--quiet",
                    "-m",
                    "test fixture",
                ),
                ("git", "clone", "--quiet", "--no-local", repository, clone),
            )
            for command in commands:
                result = run(*command)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            self.assertFalse(
                (clone / ".agents" / "notes" / "archived" / "feature").exists()
            )
            verified = self.verify(clone)
            self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)


if __name__ == "__main__":
    unittest.main()
