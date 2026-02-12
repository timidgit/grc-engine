"""Compliance scoring engine with first-scan and history-aware modes."""

from __future__ import annotations

# First-scan weights (no evidence history)
FIRST_SCAN_WEIGHTS = {
    "completeness": 0.70,
    "critical_coverage": 0.30,
}

# Full weights (with evidence history from 2+ scans)
FULL_WEIGHTS = {
    "completeness": 0.40,
    "freshness": 0.25,
    "critical_coverage": 0.20,
    "remediation_velocity": 0.15,
}


def calculate_scores(
    raw_scan: dict,
    patterns: list[dict],
    critical_controls: set[str],
) -> tuple[dict, list, list]:
    """Calculate per-regulation scores from raw scan results.

    Args:
        raw_scan: Output from scan_directory().
        patterns: All patterns used in the scan.
        critical_controls: Set of critical control IDs.

    Returns:
        Tuple of (scores_by_regulation, gaps, matches).
    """
    from grc_engine import Gap, Match, Score

    matched_controls = set(raw_scan.get("matched_controls", []))
    raw_matches = raw_scan.get("matches", [])

    matches = []
    for m in raw_matches:
        matches.append(
            Match(
                control_id=m["control_id"],
                pattern_id=m["pattern_id"],
                label=m["label"],
                file=m["file"],
                match_count=m.get("match_count", 1),
            )
        )

    # Group patterns by regulation
    by_reg: dict[str, list[dict]] = {}
    for p in patterns:
        reg = p.get("regulation", "Unknown")
        by_reg.setdefault(reg, []).append(p)

    scores_by_reg = {}
    gaps = []

    for reg, reg_patterns in sorted(by_reg.items()):
        reg_controls = {
            p["control_id"] for p in reg_patterns if p.get("control_id")
        }
        reg_matched = reg_controls & matched_controls
        reg_unmatched = reg_controls - matched_controls

        reg_critical = reg_controls & critical_controls
        reg_critical_matched = reg_matched & critical_controls

        total = len(reg_controls)
        matched = len(reg_matched)
        completeness = (matched / total * 100) if total else 0.0

        critical_total = len(reg_critical)
        critical_matched_count = len(reg_critical_matched)
        critical_pct = (
            (critical_matched_count / critical_total * 100) if critical_total else 100.0
        )

        # First-scan weighted score
        pct = (
            FIRST_SCAN_WEIGHTS["completeness"] * completeness
            + FIRST_SCAN_WEIGHTS["critical_coverage"] * critical_pct
        )

        scores_by_reg[reg] = Score(
            pct=round(pct, 1),
            matched=matched,
            total=total,
            critical_pct=round(critical_pct, 1),
        )

        # Build gap list for unmatched controls
        pattern_info: dict[str, dict] = {}
        for p in reg_patterns:
            cid = p.get("control_id")
            if cid and cid not in pattern_info:
                pattern_info[cid] = p

        for cid in sorted(reg_unmatched):
            info = pattern_info.get(cid, {})
            severity = "critical" if cid in critical_controls else "normal"
            gaps.append(
                Gap(
                    control_id=cid,
                    regulation=reg,
                    severity=severity,
                    label=info.get("label", ""),
                    description=info.get("description", ""),
                )
            )

    # Sort gaps: critical first, then by control_id
    gaps.sort(key=lambda g: (0 if g.severity == "critical" else 1, g.control_id))

    return scores_by_reg, gaps, matches
