"""grc-engine: Regulatory compliance scoring for any codebase."""

from __future__ import annotations

__version__ = "0.1.0"

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass(frozen=True)
class Match:
    """A compliance pattern match in a source file."""

    control_id: str
    pattern_id: str
    label: str
    file: str
    match_count: int = 1


@dataclass(frozen=True)
class Gap:
    """A missing compliance control."""

    control_id: str
    regulation: str
    severity: str  # "critical" or "normal"
    label: str
    description: str


@dataclass(frozen=True)
class Score:
    """Compliance score for a single regulation."""

    pct: float
    matched: int
    total: int
    critical_pct: float = 0.0


@dataclass(frozen=True)
class ScanResult:
    """Complete scan result with scores, gaps, and matches."""

    target: str
    files_scanned: int
    scores: dict  # regulation -> Score
    gaps: list  # list[Gap]
    matches: list  # list[Match]
    timestamp: str = ""

    def to_json(self) -> str:
        """Serialize to JSON string."""
        from grc_engine.report import to_json_report

        return to_json_report(self)

    def to_markdown(self) -> str:
        """Serialize to Markdown report."""
        from grc_engine.report import to_markdown_report

        return to_markdown_report(self)


def scan(
    path: str = ".",
    *,
    regulation: Optional[str] = None,
    extensions: Optional[list[str]] = None,
    max_files: int = 10000,
) -> ScanResult:
    """Scan a codebase for regulatory compliance patterns.

    Args:
        path: Directory to scan.
        regulation: Filter to a specific regulation (e.g. "DORA").
        extensions: File extensions to scan (default: common source files).
        max_files: Maximum files to scan.

    Returns:
        ScanResult with scores, gaps, and matches.
    """
    from grc_engine.patterns import load_critical_controls, load_patterns
    from grc_engine.scanner import scan_directory
    from grc_engine.scoring import calculate_scores

    patterns = load_patterns(regulation=regulation)
    critical = load_critical_controls()

    raw = scan_directory(
        directory=path,
        patterns=patterns,
        extensions=extensions,
        max_files=max_files,
    )

    scores_by_reg, gaps, matches = calculate_scores(raw, patterns, critical)

    return ScanResult(
        target=path,
        files_scanned=raw["files_scanned"],
        scores=scores_by_reg,
        gaps=gaps,
        matches=matches,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


# Re-export EvidenceStore for convenience
def EvidenceStore(db_path="./evidence.db"):  # noqa: N802
    """Create an evidence store (lazy import)."""
    from grc_engine.evidence import EvidenceStore as _Store

    return _Store(db_path)
