"""Tests for grc_engine.evidence module."""

import pytest

from grc_engine.evidence import EvidenceStore


@pytest.fixture
def store(tmp_path):
    return EvidenceStore(tmp_path / "test_evidence.db")


class TestEvidenceStore:
    def test_record_and_retrieve(self, store):
        eid = store.record_evidence(
            control_id="DORA:Article_5",
            source="test",
            file_path="app.py",
            status="pass",
        )
        assert eid
        records = store.get_evidence(control_id="DORA:Article_5")
        assert len(records) == 1
        assert records[0]["control_id"] == "DORA:Article_5"
        assert records[0]["status"] == "pass"

    def test_coverage_summary(self, store):
        store.record_evidence(control_id="DORA:Art_5", source="test", status="pass")
        store.record_evidence(control_id="DORA:Art_9", source="test", status="fail")
        store.record_evidence(control_id="ISO:A.5.1", source="test", status="pass")
        summary = store.get_coverage_summary()
        assert summary["total_controls_with_evidence"] == 3
        assert summary["passing"] == 2
        assert summary["coverage_pct"] > 0

    def test_regulation_filter(self, store):
        store.record_evidence(control_id="DORA:Art_5", source="test", status="pass")
        store.record_evidence(control_id="ISO:A.5.1", source="test", status="pass")
        summary = store.get_coverage_summary(regulation="DORA")
        assert summary["total_controls_with_evidence"] == 1

    def test_empty_store(self, store):
        records = store.get_evidence()
        assert records == []
        summary = store.get_coverage_summary()
        assert summary["total_controls_with_evidence"] == 0

    def test_auto_creates_db(self, tmp_path):
        db_path = tmp_path / "subdir" / "nested" / "evidence.db"
        store = EvidenceStore(db_path)
        assert db_path.exists()

    def test_record_scan_result(self, store):
        from grc_engine import Gap, Match, ScanResult, Score

        result = ScanResult(
            target=".",
            files_scanned=5,
            scores={"TEST": Score(pct=50.0, matched=1, total=2)},
            gaps=[],
            matches=[
                Match(
                    control_id="TEST:C1",
                    pattern_id="P1",
                    label="Test",
                    file="a.py",
                )
            ],
        )
        ids = store.record(result)
        assert len(ids) == 1
        records = store.get_evidence()
        assert len(records) == 1

    def test_history(self, store):
        store.record_evidence(control_id="DORA:Art_5", source="test", status="pass")
        history = store.history(days=1)
        assert len(history) == 1
        history_filtered = store.history(regulation="ISO", days=1)
        assert len(history_filtered) == 0
