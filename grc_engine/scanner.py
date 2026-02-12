"""Code scanner: detects compliance patterns in source files via regex."""

import logging
import os
import re
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_EXTENSIONS = frozenset(
    [".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".yaml", ".yml", ".tf"]
)

DEFAULT_EXCLUDES = frozenset(
    [
        ".git",
        "__pycache__",
        "node_modules",
        ".venv",
        "venv",
        ".tox",
        ".mypy_cache",
        ".pytest_cache",
        "dist",
        "build",
        ".eggs",
    ]
)


def scan_file(file_path: str, patterns: list[dict]) -> list[dict]:
    """Scan a single file against all patterns. Returns list of matches."""
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        return []

    try:
        content = path.read_text(errors="replace")
    except Exception:
        return []

    matches = []
    for pat in patterns:
        regex = pat.get("detection_regex")
        if not regex:
            continue

        lang = pat.get("language", "").lower()
        suffix = path.suffix.lower()
        if lang and lang != "any" and not _language_matches(lang, suffix):
            continue

        try:
            found = re.findall(regex, content, re.MULTILINE | re.IGNORECASE)
        except re.error:
            logger.warning(
                "Invalid regex in pattern %s: %s", pat.get("pattern_id"), regex
            )
            continue

        if found:
            line_num = 0
            try:
                m = re.search(regex, content, re.MULTILINE | re.IGNORECASE)
                if m:
                    line_num = content[: m.start()].count("\n") + 1
            except re.error:
                pass

            matches.append(
                {
                    "pattern_id": pat.get("pattern_id"),
                    "control_id": pat.get("control_id"),
                    "label": pat.get("label"),
                    "match_count": len(found),
                    "file": str(path),
                    "line": line_num,
                }
            )
    return matches


def scan_directory(
    directory: str,
    patterns: list[dict],
    extensions: Optional[list[str]] = None,
    exclude_dirs: Optional[list[str]] = None,
    max_files: int = 10000,
    max_seconds: float = 300.0,
) -> dict:
    """Scan all files in a directory tree.

    Returns dict with files_scanned, matches, matched/unmatched controls.
    """
    root = Path(directory)
    if not root.is_dir():
        return {
            "error": f"Not a directory: {directory}",
            "files_scanned": 0,
            "matches": [],
            "matched_controls": [],
            "unmatched_controls": [],
        }

    exclude = set(exclude_dirs or DEFAULT_EXCLUDES)
    exts = {ext.lower() for ext in (extensions or DEFAULT_EXTENSIONS)}

    all_matches: list[dict] = []
    files_scanned = 0
    started = time.monotonic()

    for current_root, dirs, files in os.walk(root, topdown=True, followlinks=False):
        if time.monotonic() - started > max_seconds:
            break

        current = Path(current_root)
        dirs[:] = [
            d for d in dirs if d not in exclude and not (current / d).is_symlink()
        ]

        for filename in files:
            if files_scanned >= max_files:
                break

            path = current / filename
            if path.is_symlink() or path.suffix.lower() not in exts:
                continue

            files_scanned += 1
            all_matches.extend(scan_file(str(path), patterns))

        if files_scanned >= max_files:
            break

    matched_controls = {m["control_id"] for m in all_matches if m.get("control_id")}
    all_controls = {p.get("control_id") for p in patterns if p.get("control_id")}
    unmatched = all_controls - matched_controls

    return {
        "files_scanned": files_scanned,
        "total_matches": len(all_matches),
        "matched_controls": sorted(matched_controls),
        "unmatched_controls": sorted(unmatched),
        "coverage_pct": (
            round(len(matched_controls) / len(all_controls) * 100, 1)
            if all_controls
            else 0.0
        ),
        "matches": all_matches,
    }


def _language_matches(language: str, suffix: str) -> bool:
    """Check if a file suffix matches the expected language."""
    lang_map = {
        "python": [".py"],
        "javascript": [".js", ".jsx", ".mjs"],
        "typescript": [".ts", ".tsx"],
        "java": [".java"],
        "go": [".go"],
        "yaml": [".yaml", ".yml"],
        "terraform": [".tf"],
        "dockerfile": ["Dockerfile", ".dockerfile"],
    }
    expected = lang_map.get(language, [])
    return not expected or suffix in expected
