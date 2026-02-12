"""Tests for grc_engine.scoring module."""

import pytest

from grc_engine import Gap, Score
from grc_engine.scoring import FIRST_SCAN_WEIGHTS, calculate_scores

SAMPLE_PATTERNS = [
    {
        "pattern_id": "P1",
        "control_id": "DORA:Art_5",
        "label": "Governance",
        "regulation": "DORA",
    },
    {
        "pattern_id": "P2",
        "control_id": "DORA:Art_9",
        "label": "Incident",
        "regulation": "DORA",
    },
    {
        "pattern_id": "P3",
        "control_id": "ISO:A.5.1",
        "label": "Policy",
        "regulation": "ISO 27001",
    },
]

CRITICAL = {"DORA:Art_9", "ISO:A.5.1"}


class TestCalculateScores:
    def test_full_coverage(self):
        raw = {
            "files_scanned": 10,
            "matched_controls": ["DORA:Art_5", "DORA:Art_9", "ISO:A.5.1"],
            "matches": [
                {
                    "control_id": "DORA:Art_5",
                    "pattern_id": "P1",
                    "label": "Governance",
                    "file": "a.py",
                },
                {
                    "control_id": "DORA:Art_9",
                    "pattern_id": "P2",
                    "label": "Incident",
                    "file": "b.py",
                },
                {
                    "control_id": "ISO:A.5.1",
                    "pattern_id": "P3",
                    "label": "Policy",
                    "file": "c.py",
                },
            ],
        }
        scores, gaps, matches = calculate_scores(raw, SAMPLE_PATTERNS, CRITICAL)
        assert scores["DORA"].pct == 100.0
        assert scores["DORA"].matched == 2
        assert scores["DORA"].total == 2
        assert scores["ISO 27001"].pct == 100.0
        assert len(gaps) == 0
        assert len(matches) == 3

    def test_partial_coverage(self):
        raw = {
            "files_scanned": 5,
            "matched_controls": ["DORA:Art_5"],
            "matches": [
                {
                    "control_id": "DORA:Art_5",
                    "pattern_id": "P1",
                    "label": "Governance",
                    "file": "a.py",
                },
            ],
        }
        scores, gaps, matches = calculate_scores(raw, SAMPLE_PATTERNS, CRITICAL)
        assert scores["DORA"].matched == 1
        assert scores["DORA"].total == 2
        assert scores["DORA"].critical_pct == 0.0
        gap_ids = {g.control_id for g in gaps}
        assert "DORA:Art_9" in gap_ids
        assert "ISO:A.5.1" in gap_ids

    def test_no_matches(self):
        raw = {"files_scanned": 0, "matched_controls": [], "matches": []}
        scores, gaps, matches = calculate_scores(raw, SAMPLE_PATTERNS, CRITICAL)
        assert scores["DORA"].pct == 0.0
        assert len(gaps) == 3

    def test_critical_gaps_sorted_first(self):
        raw = {"files_scanned": 0, "matched_controls": [], "matches": []}
        _, gaps, _ = calculate_scores(raw, SAMPLE_PATTERNS, CRITICAL)
        critical_gaps = [g for g in gaps if g.severity == "critical"]
        normal_gaps = [g for g in gaps if g.severity == "normal"]
        if critical_gaps and normal_gaps:
            assert gaps.index(critical_gaps[0]) < gaps.index(normal_gaps[0])

    def test_weights_sum_to_one(self):
        assert abs(sum(FIRST_SCAN_WEIGHTS.values()) - 1.0) < 0.001

    def test_empty_patterns(self):
        raw = {"files_scanned": 5, "matched_controls": [], "matches": []}
        scores, gaps, matches = calculate_scores(raw, [], set())
        assert scores == {}
        assert gaps == []
