#!/usr/bin/env python3
"""Install the allowlisted agent docs scaffold without overwriting files."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys


KIT_ROOT = Path(__file__).resolve().parent


TEMPLATE_ROOT = KIT_ROOT / "template"
PAYLOAD = (
    "AGENTS.md",
    "docs/AGENTS.md",
    "docs/architecture.md",
    "docs/decisions/TEMPLATE.md",
    "docs/product.md",
    "docs/specs/README.md",
    "docs/tasks/TEMPLATE.md",
    "scripts/verify_subsystem_pages.py",
)
CLAUDE_LINKS = ("CLAUDE.md", "docs/CLAUDE.md")
NEXT_STEP = (
    "record docs/architecture.md, docs/product.md, and one spec per subsystem in docs/specs/, "
    "then run python3 scripts/verify_subsystem_pages.py --map"
)
# Platform metadata that editors and interpreters drop into the kit checkout.
IGNORED_TEMPLATE_NAMES = {".DS_Store", "Thumbs.db"}
IGNORED_TEMPLATE_SUFFIXES = {".pyc"}
IGNORED_TEMPLATE_DIRECTORIES = {"__pycache__"}


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description=(
            "Preview or install the agent docs scaffold. "
            "Existing destination files are never overwritten."
        )
    )
    result.add_argument("target", type=Path, help="target repository directory")
    result.add_argument(
        "--apply",
        action="store_true",
        help="write after collision preflight; otherwise preview only",
    )
    result.add_argument(
        "--claude-symlinks",
        action="store_true",
        help="also create CLAUDE.md -> AGENTS.md links in the root and docs/",
    )
    return result


def ignored_template_entry(root: Path, path: Path) -> bool:
    """Ignore only ordinary platform metadata, never a symlink payload."""

    if path.is_symlink() or not path.is_file():
        return False
    parts = path.relative_to(root).parts
    return (
        path.name in IGNORED_TEMPLATE_NAMES
        or path.suffix in IGNORED_TEMPLATE_SUFFIXES
        or any(part in IGNORED_TEMPLATE_DIRECTORIES for part in parts[:-1])
    )


def template_files() -> tuple[Path, ...]:
    """Return the reviewed payload and reject missing or unreviewed files."""

    discovered = {
        path.relative_to(TEMPLATE_ROOT).as_posix()
        for path in TEMPLATE_ROOT.rglob("*")
        if (path.is_file() or path.is_symlink())
        and not ignored_template_entry(TEMPLATE_ROOT, path)
    }
    expected = set(PAYLOAD)
    violations = [
        *(f"missing allowlisted file: {path}" for path in sorted(expected - discovered)),
        *(f"unexpected template file: {path}" for path in sorted(discovered - expected)),
    ]
    if violations:
        raise ValueError("template payload mismatch:\n- " + "\n- ".join(violations))
    return tuple(TEMPLATE_ROOT / path for path in PAYLOAD)


def planned_directories(
    target: Path,
    template_root: Path,
    sources: tuple[Path, ...],
) -> tuple[Path, ...]:
    directories = {
        target / path.relative_to(template_root).parent
        for path in sources
    }
    return tuple(sorted(directories, key=lambda path: (len(path.parts), path.as_posix())))


def planned_files(
    target: Path,
    sources: tuple[Path, ...],
    include_claude: bool,
) -> tuple[tuple[Path, Path | str], ...]:
    files: list[tuple[Path, Path | str]] = [
        (target / source.relative_to(TEMPLATE_ROOT), source)
        for source in sources
    ]
    if include_claude:
        files.extend((target / link, "AGENTS.md") for link in CLAUDE_LINKS)
    return tuple(files)


def unsafe_target(target: Path) -> bool:
    return target == Path(target.anchor) or target == Path.home().resolve()


def directory_conflicts(target: Path, directories: tuple[Path, ...]) -> tuple[str, ...]:
    conflicts: list[str] = []
    inspected: set[Path] = set()
    for directory in directories:
        current = target
        for part in directory.relative_to(target).parts:
            current = current / part
            if current in inspected:
                continue
            inspected.add(current)
            if not os.path.lexists(current):
                continue
            if current.is_symlink():
                conflicts.append(f"{current}: existing directory path is a symlink")
            elif not current.is_dir():
                conflicts.append(f"{current}: expected a directory")
    return tuple(conflicts)


def main() -> int:
    args = parser().parse_args()
    target = args.target.expanduser().resolve()
    if not target.exists() or not target.is_dir():
        print(f"target is not an existing directory: {target}", file=sys.stderr)
        return 2
    if unsafe_target(target):
        print(f"refusing broad target: {target}", file=sys.stderr)
        return 2

    try:
        sources = template_files()
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2
    if not sources:
        print(f"template contains no files: {TEMPLATE_ROOT}", file=sys.stderr)
        return 2
    source_symlinks = [source for source in sources if source.is_symlink()]
    if source_symlinks:
        print("template contains unsupported symlinks:", file=sys.stderr)
        for source in source_symlinks:
            print(f"- {source}", file=sys.stderr)
        return 2

    try:
        payloads = {source: source.read_bytes() for source in sources}
    except OSError as error:
        print(f"cannot snapshot template payload: {error}", file=sys.stderr)
        return 2

    files = planned_files(target, sources, args.claude_symlinks)
    directories = planned_directories(target, TEMPLATE_ROOT, sources)
    path_conflicts = directory_conflicts(target, directories)
    if path_conflicts:
        print("initialization refused; unsafe destination directories:", file=sys.stderr)
        for conflict in path_conflicts:
            print(f"- {conflict}", file=sys.stderr)
        print("no files were written", file=sys.stderr)
        return 2
    collisions = [destination for destination, _ in files if os.path.lexists(destination)]
    if collisions:
        print("initialization refused; existing destinations:", file=sys.stderr)
        for destination in collisions:
            print(f"- {destination}", file=sys.stderr)
        print("adapt the existing documentation manually; no files were written", file=sys.stderr)
        return 2

    print(f"target: {target}")
    print("planned files:")
    for destination, source in files:
        kind = f"symlink -> {source}" if isinstance(source, str) else "file"
        print(f"- {destination.relative_to(target)} ({kind})")
    if not args.apply:
        print("preview only; re-run with --apply to write")
        return 0

    created_files: list[Path] = []
    created_directories: list[Path] = []
    try:
        for directory in directories:
            missing: list[Path] = []
            current = directory
            while current != target and not current.exists():
                missing.append(current)
                current = current.parent
            for candidate in reversed(missing):
                candidate.mkdir()
                created_directories.append(candidate)

        for destination, source in files:
            if isinstance(source, str):
                destination.symlink_to(source)
                created_files.append(destination)
            else:
                descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
                created_files.append(destination)
                with os.fdopen(descriptor, "wb") as handle:
                    handle.write(payloads[source])
    except (Exception, KeyboardInterrupt) as error:
        for path in reversed(created_files):
            try:
                path.unlink()
            except FileNotFoundError:
                pass
        for directory in reversed(created_directories):
            try:
                directory.rmdir()
            except OSError:
                pass
        if isinstance(error, KeyboardInterrupt):
            print("initialization interrupted; created files were rolled back", file=sys.stderr)
            return 130
        print(f"initialization failed and created files were rolled back: {error}", file=sys.stderr)
        return 1

    print(f"created {len(created_files)} files; no existing file was modified")
    print(f"next: {NEXT_STEP}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
