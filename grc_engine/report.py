"""Report generation: Rich terminal, JSON, Markdown."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from grc_engine import ScanResult

__version__ = "0.1.0"


def render_scorecard(result: ScanResult) -> None:
    """Print a Rich terminal scorecard."""
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    console = Console()

    console.print()
    console.print(
        Panel(
            f"[bold]GRC Engine v{__version__}[/bold] \u2014 Compliance Scorecard",
            border_style="blue",
        )
    )

    table = Table(show_header=True, header_style="bold", padding=(0, 2))
    table.add_column("Regulation", style="cyan", min_width=14)
    table.add_column("Score", justify="right", min_width=8)
    table.add_column("Bar", min_width=20)
    table.add_column("Critical", justify="right", min_width=10)
    table.add_column("Matched", justify="right")
    table.add_column("Total", justify="right")

    for reg, score in sorted(result.scores.items()):
        if score.pct >= 80:
            color = "green"
        elif score.pct >= 60:
            color = "yellow"
        elif score.pct >= 40:
            color = "orange1"
        else:
            color = "red"

        filled = int(score.pct / 10)
        full = "\u2588" * filled
        empty = "\u2591" * (10 - filled)
        bar = f"[{color}]{full}{empty}[/{color}]"

        table.add_row(
            reg,
            f"[{color}]{score.pct:.0f}%[/{color}]",
            bar,
            f"{score.critical_pct:.0f}%",
            str(score.matched),
            str(score.total),
        )

    console.print(table)

    critical_gaps = [g for g in result.gaps if g.severity == "critical"]
    other_gaps = [g for g in result.gaps if g.severity != "critical"]
    top_gaps = (critical_gaps + other_gaps)[:5]

    if top_gaps:
        console.print()
        console.print("[bold]Top Gaps:[/bold]")
        for i, gap in enumerate(top_gaps, 1):
            severity_tag = (
                "[red](critical)[/red]" if gap.severity == "critical" else ""
            )
            console.print(
                f"  {i}. [bold]{gap.control_id}[/bold] {severity_tag}"
                f" \u2014 {gap.description or gap.label}"
            )

    console.print()
    console.print(f"[dim]Scanned {result.files_scanned} files | {result.target}[/dim]")
    console.print()


def to_json_report(result: ScanResult) -> str:
    """Serialize a ScanResult to JSON string."""
    report = {
        "grc_engine_version": __version__,
        "timestamp": result.timestamp or datetime.now(timezone.utc).isoformat(),
        "target": result.target,
        "files_scanned": result.files_scanned,
        "scores": {
            reg: {
                "pct": score.pct,
                "matched": score.matched,
                "total": score.total,
                "critical_pct": score.critical_pct,
            }
            for reg, score in result.scores.items()
        },
        "gaps": [
            {
                "control_id": g.control_id,
                "regulation": g.regulation,
                "severity": g.severity,
                "label": g.label,
                "description": g.description,
            }
            for g in result.gaps
        ],
        "matches": [
            {
                "control_id": m.control_id,
                "pattern_id": m.pattern_id,
                "file": m.file,
                "label": m.label,
                "match_count": m.match_count,
            }
            for m in result.matches
        ],
    }
    return json.dumps(report, indent=2)


def to_markdown_report(result: ScanResult) -> str:
    """Generate a Markdown compliance report."""
    ts = result.timestamp[:10] if result.timestamp else "N/A"
    lines = [
        "# GRC Compliance Report",
        f"**Scanned:** {result.target} ({result.files_scanned} files) | {ts}",
        "",
        "| Regulation | Score | Critical | Matched | Total |",
        "| ---------- | ----- | -------- | ------- | ----- |",
    ]

    for reg, score in sorted(result.scores.items()):
        lines.append(
            f"| {reg} | {score.pct:.0f}% | {score.critical_pct:.0f}%"
            f" | {score.matched} | {score.total} |"
        )

    if result.gaps:
        lines.append("")
        lines.append("## Top Gaps")
        critical_gaps = [g for g in result.gaps if g.severity == "critical"]
        other_gaps = [g for g in result.gaps if g.severity != "critical"]
        top_gaps = (critical_gaps + other_gaps)[:10]
        for i, gap in enumerate(top_gaps, 1):
            sev = " (critical)" if gap.severity == "critical" else ""
            lines.append(
                f"{i}. **{gap.control_id}**{sev}"
                f" \u2014 {gap.description or gap.label}"
            )

    lines.append("")
    return "\n".join(lines)
