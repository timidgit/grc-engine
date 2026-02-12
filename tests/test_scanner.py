"""Tests for grc_engine.scanner module."""

import pytest

from grc_engine.scanner import _language_matches, scan_directory, scan_file

SAMPLE_PATTERNS = [
    {
        "pattern_id": "TEST-001",
        "control_id": "TEST:Control_1",
        "label": "Risk management",
        "description": "Risk management framework",
        "language": "python",
        "detection_regex": r"(?i)(risk[_\s-]?management)",
        "regulation": "TEST",
    },
    {
        "pattern_id": "TEST-002",
        "control_id": "TEST:Control_2",
        "label": "Authentication",
        "description": "Multi-factor authentication",
        "language": "any",
        "detection_regex": r"(?i)(mfa|multi[_\s-]?factor)",
        "regulation": "TEST",
    },
]


class TestScanFile:
    def test_matching_file(self, tmp_path):
        f = tmp_path / "app.py"
        f.write_text("class RiskManagement:\n    pass\n")
        matches = scan_file(str(f), SAMPLE_PATTERNS)
        assert len(matches) == 1
        assert matches[0]["control_id"] == "TEST:Control_1"

    def test_no_match(self, tmp_path):
        f = tmp_path / "empty.py"
        f.write_text("x = 1\n")
        matches = scan_file(str(f), SAMPLE_PATTERNS)
        assert len(matches) == 0

    def test_language_filter(self, tmp_path):
        f = tmp_path / "config.yaml"
        f.write_text("risk_management: true\n")
        matches = scan_file(str(f), SAMPLE_PATTERNS)
        # Pattern TEST-001 is python-only, should not match yaml
        risk_matches = [m for m in matches if m["control_id"] == "TEST:Control_1"]
        assert len(risk_matches) == 0

    def test_nonexistent_file(self):
        matches = scan_file("/nonexistent/file.py", SAMPLE_PATTERNS)
        assert matches == []

    def test_line_number_reported(self, tmp_path):
        f = tmp_path / "app.py"
        f.write_text("# header\nx = 1\nclass RiskManagement:\n    pass\n")
        matches = scan_file(str(f), SAMPLE_PATTERNS)
        assert len(matches) == 1
        assert matches[0]["line"] == 3


class TestScanDirectory:
    def test_scan_directory(self, tmp_path):
        (tmp_path / "app.py").write_text(
            "class RiskManagement:\n    require_mfa(user)\n"
        )
        (tmp_path / "test.py").write_text("x = 1\n")
        result = scan_directory(str(tmp_path), SAMPLE_PATTERNS)
        assert result["files_scanned"] == 2
        assert "TEST:Control_1" in result["matched_controls"]
        assert "TEST:Control_2" in result["matched_controls"]

    def test_extension_filter(self, tmp_path):
        (tmp_path / "app.py").write_text("risk_management = True\n")
        (tmp_path / "readme.md").write_text("# Risk Management\n")
        result = scan_directory(str(tmp_path), SAMPLE_PATTERNS, extensions=[".py"])
        assert result["files_scanned"] == 1

    def test_empty_directory(self, tmp_path):
        result = scan_directory(str(tmp_path), SAMPLE_PATTERNS)
        assert result["files_scanned"] == 0
        assert result["coverage_pct"] == 0.0

    def test_max_files(self, tmp_path):
        for i in range(10):
            (tmp_path / f"file_{i}.py").write_text(f"x = {i}\n")
        result = scan_directory(str(tmp_path), SAMPLE_PATTERNS, max_files=3)
        assert result["files_scanned"] == 3

    def test_excludes_dirs(self, tmp_path):
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "app.py").write_text("risk_management = True\n")
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "node_modules" / "lib.py").write_text("risk_management = True\n")
        result = scan_directory(str(tmp_path), SAMPLE_PATTERNS)
        assert result["files_scanned"] == 1


class TestLanguageMatches:
    def test_python(self):
        assert _language_matches("python", ".py") is True
        assert _language_matches("python", ".js") is False

    def test_any(self):
        # "any" is handled before calling _language_matches, but
        # if called, unknown languages return True
        assert _language_matches("unknown", ".py") is True

    def test_yaml(self):
        assert _language_matches("yaml", ".yaml") is True
        assert _language_matches("yaml", ".yml") is True
        assert _language_matches("yaml", ".py") is False
