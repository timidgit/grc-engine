"""Tests for grc_engine CLI."""

import json

import pytest
from click.testing import CliRunner

from grc_engine.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def sample_project(tmp_path):
    """Create a minimal project for scanning."""
    (tmp_path / "app.py").write_text(
        "class RiskManagement:\n"
        "    def assess_ict_risk(self, asset):\n"
        "        require_mfa(user)\n"
    )
    (tmp_path / "ci.yml").write_text(
        "stages: [build, test, security-scan, deploy]\n"
        "security_scan:\n"
        "  - bandit -r src/\n"
    )
    return tmp_path


class TestScanCommand:
    def test_scan_text_output(self, runner, sample_project):
        result = runner.invoke(cli, ["scan", str(sample_project)])
        assert result.exit_code == 0

    def test_scan_json_output(self, runner, sample_project):
        result = runner.invoke(
            cli, ["scan", str(sample_project), "--format", "json"]
        )
        assert result.exit_code == 0
        report = json.loads(result.output)
        assert "scores" in report
        assert "gaps" in report

    def test_scan_markdown_output(self, runner, sample_project):
        result = runner.invoke(
            cli, ["scan", str(sample_project), "--format", "markdown"]
        )
        assert result.exit_code == 0
        assert "# GRC Compliance Report" in result.output

    def test_scan_with_output_file(self, runner, sample_project, tmp_path):
        output = tmp_path / "report.json"
        result = runner.invoke(
            cli, ["scan", str(sample_project), "--output", str(output)]
        )
        assert result.exit_code == 0
        assert output.exists()

    def test_scan_regulation_filter(self, runner, sample_project):
        result = runner.invoke(
            cli,
            ["scan", str(sample_project), "--format", "json", "-r", "DORA"],
        )
        assert result.exit_code == 0
        report = json.loads(result.output)
        assert "DORA" in report["scores"]

    def test_fail_under_passes(self, runner, sample_project):
        result = runner.invoke(
            cli, ["scan", str(sample_project), "--fail-under", "0"]
        )
        assert result.exit_code == 0

    def test_fail_under_fails(self, runner, sample_project):
        result = runner.invoke(
            cli, ["scan", str(sample_project), "--fail-under", "100"]
        )
        assert result.exit_code == 1


class TestPatternsCommand:
    def test_patterns_list(self, runner):
        result = runner.invoke(cli, ["patterns", "list"])
        assert result.exit_code == 0
        assert "Total:" in result.output

    def test_patterns_list_filtered(self, runner):
        result = runner.invoke(cli, ["patterns", "list", "-r", "DORA"])
        assert result.exit_code == 0

    def test_patterns_show(self, runner):
        result = runner.invoke(cli, ["patterns", "show", "DORA:Article_5"])
        assert result.exit_code == 0
        assert "DORA:Article_5" in result.output


class TestHelpOutput:
    def test_root_help(self, runner):
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "GRC Engine" in result.output

    def test_scan_help(self, runner):
        result = runner.invoke(cli, ["scan", "--help"])
        assert result.exit_code == 0
        assert "--regulation" in result.output
        assert "--fail-under" in result.output
