"""Tests for grc_engine.report module."""

import json

import pytest

from grc_engine import Gap, Match, ScanResult, Score
from grc_engine.report import to_json_report, to_markdown_report


@pytest.fixture
def sample_result():
    return ScanResult(
        target="/test/path",
        files_scanned=42,
        scores={
            "DORA": Score(pct=72.0, matched=5, total=7, critical_pct=75.0),
            "ISO 27001": Score(pct=45.0, matched=3, total=6, critical_pct=50.0),
        },
        gaps=[
            Gap(
                control_id="DORA:Art_9",
                regulation="DORA",
                severity="critical",
                label="Incident reporting",
                description="No incident reporting detected",
            ),
            Gap(
                control_id="ISO:A.5.1",
                regulation="ISO 27001",
                severity="critical",
                label="Security policy",
                description="No security policy found",
            ),
        ],
        matches=[
            Match(
                control_id="DORA:Art_5",
                pattern_id="P1",
                label="Governance",
                file="app.py",
            ),
        ],
        timestamp="2026-02-12T00:00:00+00:00",
    )


class TestJsonReport:
    def test_valid_json(self, sample_result):
        content = to_json_report(sample_result)
        report = json.loads(content)
        assert report["grc_engine_version"] == "0.1.0"
        assert report["files_scanned"] == 42
        assert "DORA" in report["scores"]
        assert len(report["gaps"]) == 2
        assert len(report["matches"]) == 1

    def test_scores_structure(self, sample_result):
        report = json.loads(to_json_report(sample_result))
        dora = report["scores"]["DORA"]
        assert dora["pct"] == 72.0
        assert dora["matched"] == 5
        assert dora["total"] == 7

    def test_gap_fields(self, sample_result):
        report = json.loads(to_json_report(sample_result))
        gap = report["gaps"][0]
        assert "control_id" in gap
        assert "regulation" in gap
        assert "severity" in gap


class TestMarkdownReport:
    def test_contains_table(self, sample_result):
        md = to_markdown_report(sample_result)
        assert "| DORA |" in md
        assert "| ISO 27001 |" in md
        assert "72%" in md
        assert "## Top Gaps" in md

    def test_contains_header(self, sample_result):
        md = to_markdown_report(sample_result)
        assert "# GRC Compliance Report" in md
        assert "42 files" in md

    def test_empty_gaps(self):
        result = ScanResult(
            target=".",
            files_scanned=1,
            scores={"TEST": Score(pct=100.0, matched=1, total=1)},
            gaps=[],
            matches=[],
        )
        md = to_markdown_report(result)
        assert "## Top Gaps" not in md
