#!/usr/bin/env python3
"""Verify the DSH-derived Agent Note tree and file format.

This gate proves structure and format only. It does not prove that a note is
true or that product behavior, tests, data handling, or release artifacts are
correct.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
import os
from pathlib import Path
import re
import sys


ACTIVE_LIFECYCLES = ("proposed", "implemented", "rejected")
ARCHIVE = "archived"
CLASSES = (
    "feature",
    "bug-fix",
    "simplification",
    "architecture",
    "process",
    "testing",
)
NOTE_ROOT_ALLOWLIST = {"AGENTS.md", "CLAUDE.md", "README.md"}
LIFECYCLE_ROOT_ALLOWLIST = {"AGENTS.md", "CLAUDE.md"}
IGNORED_ENTRY_NAMES = {".DS_Store"}
LANGUAGE_COUNTERPART_SUFFIX = ".zh.md"

NOTE_FILENAME = re.compile(r"^(?P<date>\d{4}-\d{2}-\d{2})-.+\.md$")
H1 = re.compile(r"^# Agent Note: \S")
ARCHIVED_LINE = re.compile(r"^Archived: (?P<date>\d{4}-\d{2}-\d{2})$")
STATUS = {
    "proposed": re.compile(r"^Status: proposed$"),
    "implemented": re.compile(r"^Status: implemented$"),
    "rejected": re.compile(r"^Status: rejected — .+$"),
}
REQUIRED = {
    "proposed": ("## Proposal", "## Acceptance criteria", "## Risks"),
    "implemented": ("## Decision", "## Consequences"),
    "rejected": ("## Proposal",),
}
BANNED_IMPLEMENTED = re.compile(
    r"^## (?:Proposal\b|Plan\b|Migration plan\b|Acceptance criteria\b)",
    re.IGNORECASE,
)

PROOF_LIMIT = (
    "This check proves only Agent Note structure and format; it does not verify "
    "documentation truth, product behavior, tests, data safety, or release artifacts."
)


def relative(root: Path, path: Path) -> str:
    """Return a stable path relative to .agents/notes."""

    return path.relative_to(root).as_posix()


def directory_entries(root: Path, path: Path, errors: list[str]) -> list[Path]:
    """Read one directory and report a structural error instead of crashing."""

    try:
        return sorted(path.iterdir(), key=lambda entry: entry.name)
    except OSError as error:
        display = relative(root, path) if path != root else "."
        errors.append(f"structure: {display}/ — cannot read directory: {error}")
        return []


def valid_iso_date(raw: str) -> bool:
    """Return whether a YYYY-MM-DD token is a real calendar date."""

    try:
        date.fromisoformat(raw)
    except ValueError:
        return False
    return True


def check_note_filename(
    filename: str,
    display: str,
    category: str,
    errors: list[str],
) -> bool:
    """Validate a Note filename and its first-proposed calendar date."""

    match = NOTE_FILENAME.fullmatch(filename)
    if match is None:
        errors.append(f"{category}: {display} — filename must be yyyy-mm-dd-topic.md")
        return False
    if not valid_iso_date(match.group("date")):
        errors.append(f"{category}: {display} — filename date is not a real calendar date")
        return False
    return True


def is_ignored_metadata(entry: Path) -> bool:
    """Ignore only ordinary Finder metadata, never a directory or symlink."""

    return (
        entry.name in IGNORED_ENTRY_NAMES
        and not entry.is_symlink()
        and entry.is_file()
    )


def check_instruction_entry(root: Path, entry: Path, errors: list[str]) -> None:
    """Require canonical instruction files and exact optional CLAUDE links."""

    display = relative(root, entry)
    if entry.name == "CLAUDE.md":
        if not entry.is_symlink():
            errors.append(
                f"structure: {display} — CLAUDE.md must be a symlink to AGENTS.md"
            )
            return
        try:
            target = os.readlink(entry)
        except OSError as error:
            errors.append(f"structure: {display} — cannot read symlink: {error}")
            return
        if target != "AGENTS.md":
            errors.append(
                f"structure: {display} — CLAUDE.md must target exactly AGENTS.md"
            )
            return
        agents = entry.parent / "AGENTS.md"
        if agents.is_symlink() or not agents.is_file():
            errors.append(
                f"structure: {display} — CLAUDE.md requires a sibling regular AGENTS.md"
            )
        return
    if entry.is_symlink() or not entry.is_file():
        errors.append(f"structure: {display} — {entry.name} must be a regular file")


def walk_active_tree(root: Path, errors: list[str]) -> list[tuple[str, Path]]:
    """Validate the on-demand active lifecycle/class tree."""

    for entry in directory_entries(root, root, errors):
        if is_ignored_metadata(entry):
            continue
        if entry.name == "INDEX.md":
            errors.append(
                "structure: INDEX.md — centralized Agent Note indexes are forbidden; "
                "browse the lifecycle/class tree or search the repository"
            )
            continue
        if entry.name in NOTE_ROOT_ALLOWLIST:
            check_instruction_entry(root, entry, errors)
            continue
        if entry.name == ARCHIVE or entry.name in ACTIVE_LIFECYCLES:
            if entry.is_symlink() or not entry.is_dir():
                errors.append(f"structure: {entry.name}/ — lifecycle path must be a directory")
            continue
        if entry.is_dir() and not entry.is_symlink():
            errors.append(
                f"structure: {entry.name}/ — unknown lifecycle folder "
                f"(allowed: {', '.join(ACTIVE_LIFECYCLES)}, plus {ARCHIVE}/)"
            )
        else:
            errors.append(f"structure: {entry.name} — unexpected Agent Note root entry")

    notes: list[tuple[str, Path]] = []
    for lifecycle in ACTIVE_LIFECYCLES:
        lifecycle_root = root / lifecycle
        if not lifecycle_root.exists() and not lifecycle_root.is_symlink():
            continue
        if lifecycle_root.is_symlink() or not lifecycle_root.is_dir():
            continue
        for entry in directory_entries(root, lifecycle_root, errors):
            rel = relative(root, entry)
            if is_ignored_metadata(entry):
                continue
            if entry.name in LIFECYCLE_ROOT_ALLOWLIST:
                check_instruction_entry(root, entry, errors)
                continue
            if entry.is_symlink() or not entry.is_dir():
                errors.append(
                    f"structure: {rel} — lifecycle directories contain only "
                    "instruction files and class directories"
                )
                continue
            if entry.name not in CLASSES:
                errors.append(
                    f"structure: {rel}/ — unknown class folder {entry.name!r} "
                    f"(allowed: {', '.join(CLASSES)})"
                )
                continue
            for child in directory_entries(root, entry, errors):
                child_rel = relative(root, child)
                if is_ignored_metadata(child):
                    continue
                if child.is_symlink() or not child.is_file():
                    errors.append(
                        f"structure: {child_rel} — class directories contain regular "
                        "Agent Note files only"
                    )
                    continue
                if child.name.endswith(LANGUAGE_COUNTERPART_SUFFIX):
                    errors.append(
                        f"structure: {child_rel} — `.zh.md` counterparts are forbidden; "
                        "use one Chinese-language Agent Note with the canonical English "
                        "format tokens"
                    )
                    continue
                if not check_note_filename(child.name, child_rel, "structure", errors):
                    continue
                notes.append((lifecycle, child))
    return notes


def read_lines(path: Path, display: str, errors: list[str]) -> list[str] | None:
    """Read UTF-8 without changing the line tokens checked by the DSH gate."""

    try:
        return path.read_bytes().decode("utf-8").split("\n")
    except (OSError, UnicodeError) as error:
        errors.append(f"format: {display} — cannot read UTF-8 file: {error}")
        return None


def prose_lines(lines: list[str]) -> list[str]:
    """Exclude triple-backtick examples from structural token checks."""

    prose: list[str] = []
    in_fence = False
    for line in lines:
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            prose.append(line)
    return prose


def check_sections(
    lifecycle: str,
    lines: list[str],
    fail: Callable[[str], None],
) -> None:
    """Check lifecycle-specific headings outside fenced examples."""

    prose = prose_lines(lines)
    headings = [line.rstrip() for line in prose if line.startswith("## ")]
    if not headings or headings[0] != "## Problem":
        got = headings[0] if headings else "<none>"
        fail(f"the first section must be `## Problem` (got {got!r})")
    for required in REQUIRED[lifecycle]:
        if required not in headings:
            fail(f"missing the required `{required}` section")

    if lifecycle == "implemented":
        for heading in headings:
            if BANNED_IMPLEMENTED.match(heading):
                fail(
                    f"`{heading}` is a proposal-era heading; an implemented Agent "
                    "Note states what is (fold it into Decision/Consequences/Testing)"
                )

    if "## Alternatives considered" not in headings:
        fail("missing `## Alternatives considered`")


def check_active_note(
    root: Path,
    lifecycle: str,
    path: Path,
    errors: list[str],
) -> None:
    """Port the active Agent Note header and required-heading checks from DSH."""

    display = relative(root, path)

    def fail(message: str) -> None:
        errors.append(f"format: {display} — {message}")

    lines = read_lines(path, display, errors)
    if lines is None:
        return
    prose = prose_lines(lines)

    if H1.match(lines[0] if lines else "") is None:
        fail("line 1 must be `# Agent Note: <title>`")
    if len(lines) < 2 or lines[1] != "":
        fail("line 2 must be blank")
    if len(lines) < 3 or STATUS[lifecycle].fullmatch(lines[2]) is None:
        fail(
            f"line 3 must match the {lifecycle} status grammar "
            f"({STATUS[lifecycle].pattern})"
        )
    if len(lines) < 4 or lines[3] != "":
        fail("line 4 must be blank")

    line_three = lines[2] if len(lines) >= 3 else None
    other_statuses = [
        line for line in prose if line.startswith("Status:") and line != line_three
    ]
    if other_statuses or (line_three is not None and prose.count(line_three) > 1):
        fail("the line-3 `Status:` line must be the only one in the file")

    check_sections(lifecycle, lines, fail)


def walk_archive(root: Path, errors: list[str]) -> list[Path]:
    """Check the portable single-file subset of the DSH archive path rules."""

    archive_root = root / ARCHIVE
    if archive_root.is_symlink() or not archive_root.is_dir():
        errors.append("archive: archived/ — required archive directory is missing")
        return []

    entries = directory_entries(root, archive_root, errors)
    archive_agents = archive_root / "AGENTS.md"
    if archive_agents.is_symlink() or not archive_agents.is_file():
        errors.append("archive: archived/AGENTS.md — required file is missing")

    notes: list[Path] = []
    for entry in entries:
        rel = relative(root, entry)
        if is_ignored_metadata(entry):
            continue
        if entry.is_symlink():
            errors.append(
                f"archive: {rel} — only regular files and class directories are allowed"
            )
            continue
        if entry.is_file():
            if entry.name != "AGENTS.md":
                errors.append(f"archive: {rel} — unexpected archive-root file")
            continue
        if not entry.is_dir():
            errors.append(
                f"archive: {rel} — only regular files and class directories are allowed"
            )
            continue
        if entry.name not in CLASSES:
            errors.append(f"archive: {rel}/ — unknown Agent Note class")
            continue

        for child in directory_entries(root, entry, errors):
            child_rel = relative(root, child)
            if is_ignored_metadata(child):
                continue
            if child.is_symlink() or not child.is_file():
                errors.append(
                    f"archive: {child_rel} — archive class directories contain "
                    "regular files only"
                )
                continue
            if child.name.endswith(LANGUAGE_COUNTERPART_SUFFIX):
                errors.append(
                    f"archive: {child_rel} — `.zh.md` counterparts are forbidden; "
                    "archive the single Chinese-language Agent Note"
                )
                continue
            if not check_note_filename(child.name, child_rel, "archive", errors):
                continue
            notes.append(child)
    return notes


def check_archived_note(root: Path, path: Path, errors: list[str]) -> None:
    """Check the archive header and implemented-note section skeleton."""

    display = relative(root, path)

    def fail(message: str) -> None:
        errors.append(f"archive: {display} — {message}")

    lines = read_lines(path, display, errors)
    if lines is None:
        return
    if H1.match(lines[0] if lines else "") is None:
        fail("line 1 must be `# Agent Note: <title>`")
    if len(lines) < 2 or lines[1] != "":
        fail("line 2 must be blank")
    if len(lines) < 3 or lines[2] != "Status: implemented":
        fail("line 3 must be `Status: implemented`")
    archive_match = ARCHIVED_LINE.fullmatch(lines[3]) if len(lines) >= 4 else None
    if archive_match is None:
        fail("line 4 must be `Archived: YYYY-MM-DD`")
    elif not valid_iso_date(archive_match.group("date")):
        fail("line 4 archive date is not a real calendar date")
    if len(lines) < 5 or lines[4] != "":
        fail("line 5 must be blank")
    check_sections("implemented", lines, fail)


def main() -> int:
    """Run the structural and format-only verifier."""

    repository = Path(__file__).resolve().parent.parent
    root = repository / ".agents" / "notes"
    errors: list[str] = []
    if root.is_symlink() or not root.is_dir():
        errors.append("structure: .agents/notes/ — required regular directory is missing")
        active_notes: list[tuple[str, Path]] = []
        archived_notes: list[Path] = []
    else:
        for required in (root / "AGENTS.md", root / "README.md"):
            if required.is_symlink() or not required.is_file():
                errors.append(
                    f"structure: {relative(root, required)} — required regular file is missing"
                )
        implemented_agents = root / "implemented" / "AGENTS.md"
        if implemented_agents.is_symlink() or not implemented_agents.is_file():
            errors.append(
                "structure: implemented/AGENTS.md — required regular file is missing"
            )
        active_notes = walk_active_tree(root, errors)
        archived_notes = walk_archive(root, errors)

    for lifecycle, path in active_notes:
        check_active_note(root, lifecycle, path, errors)
    for path in archived_notes:
        check_archived_note(root, path, errors)

    if errors:
        print("verify_agent_notes: violations found:", file=sys.stderr)
        for error in errors:
            print(f"  {error}", file=sys.stderr)
        print(PROOF_LIMIT, file=sys.stderr)
        return 1

    print(
        "verify_agent_notes: "
        f"{len(active_notes)} active and {len(archived_notes)} archived Agent Note(s) "
        "checked; structure and format conform."
    )
    print(PROOF_LIMIT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
