#!/usr/bin/env python3
"""Verify the spec tree and map repository paths to its pages.

The spec tree is recursive. `docs/architecture.md` is the root node's map and
`docs/specs/` holds its pages. A page is either `specs/<name>.md` or a node,
`specs/<name>/`, which holds only `architecture.md` (the node's page and map)
and its own `specs/` folder of pages, shaped like the root.

Default mode checks structure only: each map's table lists every page of its
node exactly once; each page starts with a `Source:` line (`Source: none` marks
a cross-cutting page that owns no paths); each declared path or glob matches
something and is declared once; every page inside a node declares only paths
the node's `architecture.md` covers; and relative links in the spec tree
resolve inside the repository. It does not prove that a page describes the code correctly. It also
prints notes for pages and maps above their word guides; notes never fail.

`--owner PATH...` prints the page that owns each path. A file path beats a glob,
a glob beats a directory, and a longer directory beats a shorter one.
`--changed [BASE]` lists pages whose owned paths differ from BASE (default HEAD,
including staged, unstaged, and untracked files) while the page itself does
not; it exits 0 because an unchanged page can still be correct.

The root AGENTS.md carries a generated path-to-page table between the
`subsystem-map` markers. The default check fails when that table is stale;
`--map` rewrites it; the check compares cells, so a formatter may realign the
table. `--pointers` lists pages that no owned non-Markdown file names; it exits
0 because some owned files cannot hold comments.

`--split PAGE` turns a page into a node: it moves `specs/<name>.md` to
`specs/<name>/architecture.md`, creates `specs/<name>/specs/`, rewrites
relative Markdown links to and from the page, and rewrites the page's
repository path in non-Markdown files such as pointer comments. The tree fails
the default check until the node lists at least one page of its own.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import functools
import os
from pathlib import Path
import re
import subprocess
import sys


REPOSITORY = Path(__file__).resolve().parent.parent
DOCS = REPOSITORY / "docs"
# The root node's map and pages folder. Every node names its pages folder like
# the root's; a repository that keeps pages in `docs/subsystems/` sets it here.
ROOT_MAP = DOCS / "architecture.md"
PAGES = DOCS / "specs"
NODE_MAP = "architecture.md"
AGENTS_FILE = REPOSITORY / "AGENTS.md"
MAP_START = "<!-- subsystem-map:start"
MAP_END = "<!-- subsystem-map:end -->"
# Word guides: a page above PAGE_WORDS is a split candidate; a map above
# MAP_WORDS carries detail that belongs on its pages. CJK characters count as words.
PAGE_WORDS = 4000
MAP_WORDS = 2500
IGNORED_ENTRY_NAMES = {".DS_Store", "Thumbs.db"}
POINTER_SIZE_LIMIT = 1_000_000
PROOF_LIMIT = (
    "verify_subsystem_pages proves map, layout, link, and Source-path consistency "
    "only; it does not prove that page content matches the code."
)

TABLE_LINK = re.compile(r"^\|\s*\[[^\]]+\]\((?P<target>[^)#\s]+)(?:#[^)]*)?\)\s*\|")
H1 = re.compile(r"^# \S")
SOURCE_LINE = re.compile(r"^Source: (?:(?P<none>none)|(?P<paths>`[^`]+`(?:, `[^`]+`)*))$")
SOURCE_PATH = re.compile(r"`([^`]+)`")
MARKDOWN_LINK = re.compile(r"(\]\()([^)\s<>]+)((?:\s+\"[^\"]*\")?\))")
FENCE = re.compile(r"^\s*(```|~~~)")
WORD = re.compile(r"[A-Za-z0-9_]+|[぀-ヿ㐀-鿿가-힯]")
GLOB_CHARACTERS = set("*?[")


@dataclass
class Page:
    """One page of the spec tree: a single Markdown page or a node's architecture.md."""

    path: Path
    parent: Page | None
    is_node: bool
    sources: list[str] = field(default_factory=list)
    declares_none: bool = False

    @property
    def key(self) -> str:
        return display(self.path)

    @property
    def label(self) -> str:
        """Name the page by its position in the tree, such as `cli` or `cli/shot`."""

        names: list[str] = []
        page: Page | None = self
        while page is not None:
            names.append(page.path.parent.name if page.is_node else page.path.stem)
            page = page.parent
        return "/".join(reversed(names))


def display(path: Path) -> str:
    return Path(os.path.normpath(path)).relative_to(REPOSITORY).as_posix()


def word_count(path: Path) -> int:
    return len(WORD.findall(path.read_text(encoding="utf-8")))


def outside_code(line: str) -> list[tuple[int, int]]:
    """Return the spans of a line that lie outside inline code."""

    spans: list[tuple[int, int]] = []
    start = 0
    inside = False
    for index, character in enumerate(line):
        if character == "`":
            if not inside:
                spans.append((start, index))
            inside = not inside
            start = index + 1
    if not inside:
        spans.append((start, len(line)))
    return spans


def markdown_links(text: str):
    """Yield (line number, match) for inline links outside fenced and inline code."""

    fenced = False
    for number, line in enumerate(text.splitlines(), 1):
        if FENCE.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        for start, end in outside_code(line):
            for match in MARKDOWN_LINK.finditer(line, start, end):
                yield number, match


def is_relative_target(target: str) -> bool:
    return not (
        target.startswith(("#", "/"))
        or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target)
    )


def split_target(target: str) -> tuple[str, str]:
    path, hash_mark, fragment = target.partition("#")
    return path, hash_mark + fragment


def resolve_link(base: Path, target: str) -> Path:
    path, _ = split_target(target)
    if path.startswith("./"):
        path = path[2:]
    return Path(os.path.normpath(base / path))


def map_rows(map_file: Path, pages_dir: Path, errors: list[str]) -> list[Path]:
    """Return the page files a map's table rows link inside its pages folder, in order."""

    rows: list[Path] = []
    for number, line in enumerate(map_file.read_text(encoding="utf-8").splitlines(), 1):
        match = TABLE_LINK.match(line)
        if not match:
            continue
        target = resolve_link(map_file.parent, match.group("target"))
        try:
            relative = target.relative_to(pages_dir)
        except ValueError:
            continue
        parts = relative.parts
        direct = (len(parts) == 1 and target.suffix == ".md") or (
            len(parts) == 2 and parts[1] == NODE_MAP
        )
        if not direct:
            errors.append(
                f"map: {display(map_file)}:{number} — {display(target)} is not a page of this node; "
                "link `<name>.md` or `<name>/architecture.md` in its own node's map"
            )
            continue
        if target in rows:
            errors.append(f"map: {display(map_file)}:{number} — {display(target)} is listed twice")
            continue
        rows.append(target)
    return rows


def node_pages(pages_dir: Path, is_root: bool, errors: list[str]) -> list[tuple[Path, bool]]:
    """Return (page file, is node) for each entry of a pages folder and report other entries."""

    pages: list[tuple[Path, bool]] = []
    for entry in sorted(pages_dir.iterdir()):
        if entry.name in IGNORED_ENTRY_NAMES:
            continue
        if entry.is_symlink():
            errors.append(f"structure: {display(entry)} — symlinks are not allowed in the spec tree")
        elif entry.is_file():
            if entry.suffix != ".md":
                errors.append(f"structure: {display(entry)} — only Markdown pages and node folders are allowed")
            elif is_root and entry.name == "README.md":
                errors.append(
                    f"structure: {display(entry)} — the index lives in {display(ROOT_MAP)}; "
                    "move its rows there and its page rules to docs/AGENTS.md"
                )
            elif is_root and entry.name == NODE_MAP:
                errors.append(f"structure: {display(entry)} — move the root map to {display(ROOT_MAP)}")
            else:
                pages.append((entry, False))
        elif entry.is_dir():
            node_map = entry / NODE_MAP
            for inner in sorted(entry.iterdir()):
                if inner.name in IGNORED_ENTRY_NAMES or inner.name in {NODE_MAP, pages_dir.name}:
                    continue
                errors.append(
                    f"structure: {display(inner)} — a node holds only {NODE_MAP} and {pages_dir.name}/; "
                    "decisions, tasks, and research stay in the root docs/"
                )
            if node_map.is_symlink() or not node_map.is_file():
                errors.append(f"structure: {display(entry)}/ — a node needs {NODE_MAP}")
            else:
                pages.append((node_map, True))
    return pages


def page_sources(page: Page, errors: list[str]) -> None:
    """Read the `Source:` line of a page into page.sources."""

    path = page.path
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or not H1.match(lines[0]):
        errors.append(f"page: {display(path)}:1 — first line must be a `# ` title")
        return
    following = [(number, line) for number, line in enumerate(lines[1:], 2) if line.strip()]
    if not following:
        errors.append(f"page: {display(path)} — missing `Source:` line after the title")
        return
    number, line = following[0]
    match = SOURCE_LINE.match(line)
    if not match:
        errors.append(
            f"page: {display(path)}:{number} — first line after the title must be "
            "`Source: `path/`, `file`` or `Source: none`"
        )
        return
    if match.group("none"):
        page.declares_none = True
        return
    for raw in SOURCE_PATH.findall(match.group("paths")):
        if raw.startswith("/") or ".." in Path(raw).parts or raw in {".", "./"}:
            errors.append(f"page: {display(path)}:{number} — {raw} must be repository-relative")
            continue
        if is_glob(raw):
            if raw.endswith("/"):
                errors.append(f"page: {display(path)}:{number} — glob {raw} must match files")
            elif not any(glob_pattern(raw).match(file) for file in repository_files()):
                errors.append(f"page: {display(path)}:{number} — glob {raw} matches no file")
            else:
                page.sources.append(raw)
            continue
        target = REPOSITORY / raw
        if not target.exists():
            errors.append(f"page: {display(path)}:{number} — {raw} does not exist")
            continue
        if target.is_dir() != raw.endswith("/"):
            errors.append(
                f"page: {display(path)}:{number} — {raw}: directories end with `/`, files do not"
            )
            continue
        page.sources.append(raw)


def walk(map_file: Path, pages_dir: Path, parent: Page | None, pages: list[Page], errors: list[str]) -> None:
    """Check one node and recurse into its child nodes, appending pages depth-first."""

    if not pages_dir.is_dir() or pages_dir.is_symlink():
        if parent is not None:
            errors.append(
                f"structure: {display(pages_dir)}/ — a node needs a {pages_dir.name}/ folder with its pages"
            )
        return
    found = node_pages(pages_dir, parent is None, errors)
    if parent is not None and not found:
        errors.append(
            f"structure: {display(pages_dir)}/ — the node has no pages; "
            f"turn {display(pages_dir.parent)}/{NODE_MAP} back into {display(pages_dir.parent)}.md"
        )
    rows = map_rows(map_file, pages_dir, errors)
    files = {path: is_node for path, is_node in found}
    for path in files:
        if path not in rows:
            errors.append(f"map: {display(path)} — page is missing from the table in {display(map_file)}")
    for row in rows:
        if row not in files:
            errors.append(f"map: {display(map_file)} links {display(row)}, which does not exist")
    for path in [row for row in rows if row in files] + sorted(p for p in files if p not in rows):
        page = Page(path=path, parent=parent, is_node=files[path])
        page_sources(page, errors)
        pages.append(page)
        if page.is_node:
            walk(path, path.parent / pages_dir.name, page, pages, errors)


def check_containment(pages: list[Page], errors: list[str]) -> None:
    """Require every page inside a node to declare only paths its node covers."""

    for page in pages:
        node = page.parent
        if node is None or not page.sources:
            continue
        if node.declares_none:
            errors.append(
                f"ownership: {page.key} declares paths, but its node {node.key} declares `Source: none`"
            )
            continue
        outside = [
            file
            for file in repository_files()
            if any(specificity(source, file) for source in page.sources)
            and not any(specificity(source, file) for source in node.sources)
        ]
        if outside:
            shown = ", ".join(outside[:3]) + (" …" if len(outside) > 3 else "")
            errors.append(f"ownership: {page.key} declares paths outside its node {node.key}: {shown}")


def check_links(pages: list[Page], errors: list[str]) -> None:
    """Require relative links in the root map and every page to resolve."""

    for path in [ROOT_MAP, *(page.path for page in pages)]:
        if not path.is_file():
            continue
        for number, match in markdown_links(path.read_text(encoding="utf-8")):
            target = match.group(2)
            if not is_relative_target(target) or not split_target(target)[0]:
                continue
            resolved = resolve_link(path.parent, target)
            # A link that leaves the repository depends on the machine's checkout layout.
            if REPOSITORY in resolved.parents and not resolved.exists():
                errors.append(f"link: {display(path)}:{number} — {target} does not exist")


def load(errors: list[str]) -> tuple[dict[str, str], list[Page]]:
    """Check the tree; return source path -> page key and the pages in depth-first map order."""

    if ROOT_MAP.is_symlink() or not ROOT_MAP.is_file():
        errors.append(f"structure: {display(ROOT_MAP)} — required regular file is missing")
        return {}, []
    pages: list[Page] = []
    walk(ROOT_MAP, PAGES, None, pages, errors)
    owners: dict[str, str] = {}
    for page in pages:
        for source in page.sources:
            previous = owners.get(source)
            if previous is not None and previous != page.key:
                errors.append(f"ownership: {source} is declared by both {previous} and {page.key}")
                continue
            owners[source] = page.key
    check_containment(pages, errors)
    check_links(pages, errors)
    return owners, pages


def map_lines(pages: list[Page]) -> list[str]:
    """Return the generated path-to-page table for the root AGENTS.md."""

    lines = ["| Paths | Page |", "|---|---|"]
    for page in pages:
        if page.sources:
            paths = ", ".join(f"`{source}`" for source in page.sources)
            lines.append(f"| {paths} | [{page.label}]({page.key}) |")
    return lines


def table_cells(lines: list[str]) -> list[list[str]]:
    """Return table rows as stripped cells, so formatter alignment and separator width do not matter."""

    rows: list[list[str]] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if all(re.fullmatch(r":?-+:?", cell) for cell in cells):
            cells = ["---"] * len(cells)
        rows.append(cells)
    return rows


def map_block(lines: list[str]) -> tuple[int, int] | None:
    """Return the line indexes of the map markers, or None when AGENTS.md has none."""

    starts = [number for number, line in enumerate(lines) if line.startswith(MAP_START)]
    ends = [number for number, line in enumerate(lines) if line.strip() == MAP_END]
    if not starts and not ends:
        return None
    if len(starts) != 1 or len(ends) != 1 or ends[0] < starts[0]:
        raise ValueError(f"{display(AGENTS_FILE)} must hold one `{MAP_START}` line followed by one `{MAP_END}` line")
    return starts[0], ends[0]


def check_map(pages: list[Page], errors: list[str]) -> None:
    if not AGENTS_FILE.is_file():
        return
    lines = AGENTS_FILE.read_text(encoding="utf-8").splitlines()
    try:
        block = map_block(lines)
    except ValueError as error:
        errors.append(f"map: {error}")
        return
    if block is not None and table_cells(lines[block[0] + 1 : block[1]]) != table_cells(map_lines(pages)):
        errors.append(
            f"map: {display(AGENTS_FILE)} subsystem table is stale; "
            f"run `python3 {display(Path(__file__).resolve())} --map`"
        )


def write_map(pages: list[Page]) -> int:
    lines = AGENTS_FILE.read_text(encoding="utf-8").splitlines() if AGENTS_FILE.is_file() else []
    try:
        block = map_block(lines)
    except ValueError as error:
        print(f"verify_subsystem_pages: {error}", file=sys.stderr)
        return 1
    if block is None:
        print(
            f"verify_subsystem_pages: {display(AGENTS_FILE)} has no `{MAP_START}` / `{MAP_END}` markers",
            file=sys.stderr,
        )
        return 1
    generated = map_lines(pages)
    if table_cells(lines[block[0] + 1 : block[1]]) == table_cells(generated):
        print(f"verify_subsystem_pages: {display(AGENTS_FILE)} subsystem table is current.")
        return 0
    lines[block[0] + 1 : block[1]] = generated
    AGENTS_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"verify_subsystem_pages: updated the subsystem table in {display(AGENTS_FILE)}.")
    return 0


def word_notes(pages: list[Page]) -> list[str]:
    notes: list[str] = []
    for path, is_map in [(ROOT_MAP, True), *((page.path, page.is_node) for page in pages)]:
        words = word_count(path)
        if is_map and words > MAP_WORDS:
            notes.append(
                f"{display(path)} has {words} words (map guide {MAP_WORDS}); "
                "move per-part detail onto its pages"
            )
        elif not is_map and words > PAGE_WORDS:
            notes.append(
                f"{display(path)} has {words} words (page guide {PAGE_WORDS}); "
                "split it if its parts own different files, otherwise condense it"
            )
    return notes


def text_files(markdown: bool) -> list[Path]:
    """Return repository text files of one kind that are small enough to rewrite."""

    result: list[Path] = []
    for file in repository_files():
        if file.endswith((".md", ".mdx")) != markdown:
            continue
        path = REPOSITORY / file
        try:
            if path.is_symlink() or not path.is_file() or path.stat().st_size > POINTER_SIZE_LIMIT:
                continue
        except OSError:
            continue
        result.append(path)
    return result


def rewrite_links(text: str, old_base: Path, new_base: Path, moved_from: Path, moved_to: Path) -> tuple[str, int]:
    """Rewrite relative link targets for a file read at old_base and stored at new_base."""

    lines = text.split("\n")
    count = 0
    fenced = False
    for index, line in enumerate(lines):
        if FENCE.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        pieces: list[str] = []
        cursor = 0
        for start, end in outside_code(line):
            for match in MARKDOWN_LINK.finditer(line, start, end):
                target = match.group(2)
                if not is_relative_target(target) or not split_target(target)[0]:
                    continue
                path, fragment = split_target(target)
                resolved = resolve_link(old_base, target)
                if resolved == moved_from:
                    resolved = moved_to
                elif old_base == new_base:
                    continue
                rewritten = os.path.relpath(resolved, new_base).replace(os.sep, "/")
                if path.endswith("/") and not rewritten.endswith("/"):
                    rewritten += "/"
                if rewritten + fragment == target:
                    continue
                pieces.append(line[cursor : match.start(2)] + rewritten + fragment)
                cursor = match.end(2)
                count += 1
        if pieces:
            lines[index] = "".join(pieces) + line[cursor:]
    return "\n".join(lines), count


def split_page(raw: str, pages: list[Page]) -> int:
    """Turn a single page into a node and rewrite references to it."""

    old = REPOSITORY / repository_relative(raw)
    page = next((page for page in pages if page.path == old), None)
    if page is None or page.is_node:
        print(f"verify_subsystem_pages: {raw} is not a single page of the spec tree", file=sys.stderr)
        return 2
    node = old.with_suffix("")
    new = node / NODE_MAP
    if os.path.lexists(node):
        print(f"verify_subsystem_pages: {display(node)} already exists", file=sys.stderr)
        return 2

    old_key, new_key = display(old), display(new)
    markdown = text_files(markdown=True)
    others = [path for path in text_files(markdown=False)]
    link_count = link_files = 0
    rewritten: dict[Path, str] = {}
    for path in markdown:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if path == old:
            updated, count = rewrite_links(text, old.parent, new.parent, old, new)
        else:
            updated, count = rewrite_links(text, path.parent, path.parent, old, new)
        if count:
            rewritten[path] = updated
            link_count += count
            link_files += 1
    pointer_count = pointer_files = 0
    pointer_text: dict[Path, str] = {}
    for path in others:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if old_key in text:
            pointer_count += text.count(old_key)
            pointer_files += 1
            pointer_text[path] = text.replace(old_key, new_key)

    node.mkdir()
    (node / PAGES.name).mkdir()
    os.replace(old, new)
    for path, text in rewritten.items():
        (new if path == old else path).write_text(text, encoding="utf-8")
    for path, text in pointer_text.items():
        path.write_text(text, encoding="utf-8")

    mentions = sorted(
        display(path if path != old else new)
        for path in markdown
        if (new if path == old else path).is_file()
        and old_key in (new if path == old else path).read_text(encoding="utf-8")
    )
    print(f"verify_subsystem_pages: moved {old_key} -> {new_key}")
    print(f"  rewrote {link_count} link(s) in {link_files} Markdown file(s)")
    print(f"  rewrote {pointer_count} path mention(s) in {pointer_files} other file(s)")
    if mentions:
        print(f"  review plain-text mentions of {old_key} in: {', '.join(mentions)}")
    print(
        f"next: add pages in {display(node / PAGES.name)}/, list each in the table in {new_key}, "
        "move each part's text and Source paths onto its page, then run --map"
    )
    return 0


@functools.lru_cache(maxsize=None)
def is_glob(source: str) -> bool:
    """Treat a source as a glob only when it has glob characters and is not an existing path.

    Literal directory names such as Next.js `[slug]/` or `[...key]/` stay literal paths.
    """

    if not GLOB_CHARACTERS & set(source):
        return False
    return not (REPOSITORY / source).exists()


@functools.lru_cache(maxsize=None)
def glob_pattern(source: str) -> re.Pattern[str]:
    """Translate a Source glob: `*` and `?` stay within one path segment, `**` crosses segments."""

    pattern = ""
    index = 0
    while index < len(source):
        if source.startswith("**/", index):
            pattern += "(?:.*/)?"
            index += 3
        elif source.startswith("**", index):
            pattern += ".*"
            index += 2
        elif source[index] == "*":
            pattern += "[^/]*"
            index += 1
        elif source[index] == "?":
            pattern += "[^/]"
            index += 1
        elif source[index] == "[":
            end = source.find("]", index + 1)
            if end == -1:
                pattern += re.escape("[")
                index += 1
            else:
                pattern += "[" + source[index + 1 : end].replace("\\", "\\\\") + "]"
                index = end + 1
        else:
            pattern += re.escape(source[index])
            index += 1
    return re.compile(pattern + r"\Z")


_repository_files: list[str] | None = None


def repository_files() -> list[str]:
    """Return tracked and untracked non-ignored files, or a filesystem walk outside Git."""

    global _repository_files
    if _repository_files is None:
        try:
            _repository_files = git_lines("ls-files", "--cached", "--others", "--exclude-standard")
        except (OSError, RuntimeError):
            _repository_files = [
                file.relative_to(REPOSITORY).as_posix()
                for file in REPOSITORY.rglob("*")
                if file.is_file() and ".git" not in file.relative_to(REPOSITORY).parts
            ]
        _repository_files = [file for file in _repository_files if (REPOSITORY / file).exists()]
    return _repository_files


def specificity(source: str, path: str) -> tuple[int, int] | None:
    """Rank how specifically source covers path, or return None when it does not."""

    if is_glob(source):
        return (1, len(source)) if glob_pattern(source).match(path) else None
    if source.endswith("/"):
        if path.startswith(source) or path == source.rstrip("/"):
            return (0, len(source))
        return None
    return (2, len(source)) if path == source else None


def owner_of(path: str, owners: dict[str, str]) -> str | None:
    """Return the page whose declared source most specifically covers path."""

    best: tuple[tuple[int, int], str] | None = None
    for source, page in owners.items():
        rank = specificity(source, path)
        if rank is not None and (best is None or rank > best[0]):
            best = (rank, page)
    return None if best is None else best[1]


def repository_relative(raw: str) -> str:
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    for resolved in (Path(os.path.normpath(candidate)), candidate.resolve()):
        try:
            return resolved.relative_to(REPOSITORY).as_posix()
        except ValueError:
            continue
    return raw


def git_lines(*args: str) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=REPOSITORY,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return [line for line in result.stdout.splitlines() if line]


def changed_paths(base: str) -> set[str]:
    return {
        *git_lines("diff", "--name-only", "--relative", base, "--"),
        *git_lines("ls-files", "--others", "--exclude-standard"),
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = result.add_mutually_exclusive_group()
    mode.add_argument("--owner", nargs="+", metavar="PATH", help="print the page owning each path")
    mode.add_argument("--map", action="store_true", help="rewrite the subsystem table in the root AGENTS.md")
    mode.add_argument("--pointers", action="store_true", help="list pages that no owned file names in a comment")
    mode.add_argument(
        "--changed",
        nargs="?",
        const="HEAD",
        metavar="BASE",
        help="list pages whose owned paths changed against BASE (default HEAD)",
    )
    mode.add_argument("--split", metavar="PAGE", help="turn a single page into a node")
    return result


def main() -> int:
    args = parser().parse_args()
    errors: list[str] = []
    owners, pages = load(errors)
    if not errors and not args.map:
        check_map(pages, errors)
    if errors:
        print("verify_subsystem_pages: violations found:", file=sys.stderr)
        for error in errors:
            print(f"  {error}", file=sys.stderr)
        print(PROOF_LIMIT, file=sys.stderr)
        return 1

    if args.map:
        return write_map(pages)

    if args.split:
        return split_page(args.split, pages)

    if args.pointers:
        pointed: set[str] = set()
        for file in repository_files():
            page = owner_of(file, owners)
            if page is None or page in pointed or file.endswith((".md", ".mdx")):
                continue
            path = REPOSITORY / file
            try:
                if path.stat().st_size > POINTER_SIZE_LIMIT:
                    continue
                if page in path.read_text(encoding="utf-8"):
                    pointed.add(page)
            except (OSError, UnicodeDecodeError):
                continue
        missing = [page.key for page in pages if page.sources and page.key not in pointed]
        if not missing:
            print("verify_subsystem_pages: every owning page is named by at least one file it owns.")
            return 0
        print("verify_subsystem_pages: add a comment naming the page to one entry file each of:")
        for key in missing:
            print(f"  {key}")
        return 0

    if args.owner:
        for raw in args.owner:
            path = repository_relative(raw)
            page = owner_of(path, owners)
            print(f"{path} -> " + (page if page else "(no subsystem page)"))
        return 0

    if args.changed:
        try:
            changed = changed_paths(args.changed)
        except RuntimeError as error:
            print(f"verify_subsystem_pages: {error}", file=sys.stderr)
            return 2
        stale: dict[str, list[str]] = {}
        for path in sorted(changed):
            page = owner_of(path, owners)
            if page is not None and page not in changed:
                stale.setdefault(page, []).append(path)
        if not stale:
            print(f"verify_subsystem_pages: no owned paths changed without their page against {args.changed}.")
            return 0
        print(f"verify_subsystem_pages: review these pages; their owned paths changed against {args.changed}:")
        for page, paths in sorted(stale.items()):
            print(f"  {page}: {', '.join(paths)}")
        print("Update each page whose documented facts changed; an unchanged page can still be correct.")
        return 0

    nodes = sum(1 for page in pages if page.is_node)
    print(
        f"verify_subsystem_pages: {len(set(owners.values()))} owning page(s) with {len(owners)} "
        f"source path(s) in {len(pages)} page(s), {nodes} of them node(s), under {display(PAGES)}/; "
        "maps, layout, links, and Source paths conform."
    )
    for note in word_notes(pages):
        print(f"note: {note}")
    print(PROOF_LIMIT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
