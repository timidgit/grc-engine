"""Load compliance patterns from bundled JSON data."""

import json
from pathlib import Path
from typing import Optional

_DATA_DIR = Path(__file__).parent / "data"
_PATTERNS_FILE = _DATA_DIR / "patterns.json"
_CRITICAL_CONTROLS_FILE = _DATA_DIR / "critical_controls.json"


def load_patterns(
    regulation: Optional[str] = None,
    path: Optional[Path] = None,
) -> list[dict]:
    """Load compliance patterns, optionally filtered by regulation.

    Args:
        regulation: Filter to patterns for this regulation (e.g. "DORA").
        path: Custom path to patterns JSON file.

    Returns:
        List of pattern dicts with keys: pattern_id, control_id, label,
        description, language, detection_regex, regulation.
    """
    source = path or _PATTERNS_FILE
    if not source.exists():
        return []

    with open(source) as f:
        patterns = json.load(f)

    if regulation:
        patterns = [p for p in patterns if p.get("regulation") == regulation]

    return patterns


def load_critical_controls(path: Optional[Path] = None) -> set[str]:
    """Load the set of critical control IDs."""
    source = path or _CRITICAL_CONTROLS_FILE
    if not source.exists():
        return set()
    with open(source) as f:
        return set(json.load(f))


def list_regulations() -> list[str]:
    """Return sorted list of available regulations."""
    patterns = load_patterns()
    return sorted({p.get("regulation", "") for p in patterns if p.get("regulation")})


def get_pattern_detail(control_id: str) -> list[dict]:
    """Get all patterns for a specific control ID."""
    patterns = load_patterns()
    return [p for p in patterns if p.get("control_id") == control_id]
