# grc-engine

**Regulatory compliance scoring for any codebase in under 60 seconds.**

```bash
pip install grc-engine
grc scan .
```

## Quickstart

```bash
# Install
pip install grc-engine

# Scan your codebase
grc scan .

# Output:
#   GRC Engine v0.1.0 — Compliance Scorecard
#   ─────────────────────────────────────────
#   DORA          ████████░░  72%  (5/7 controls matched)
#   ISO 27001     ████░░░░░░  45%  (3/6 controls matched)
#   AI Act        ███░░░░░░░  31%  (2/6 controls matched)
#
#   Top Gaps:
#   1. DORA:Article_9 (critical) — No ICT incident reporting detected
#   2. ISO27001:A.8.25 (critical) — No secure development lifecycle
```

## Features

- **62 compliance patterns** across 3 regulations (DORA, ISO 27001, AI Act)
- **Zero external dependencies** — SQLite + regex, no API keys, no config
- **< 60 second scans** — regex-based pattern matching, not LLM inference
- **CI/CD ready** — `grc scan . --fail-under 80` as a quality gate
- **Three output formats** — Rich terminal scorecard, JSON, Markdown

## Supported Regulations

| Regulation | Patterns | Status |
| ---------- | -------- | ------ |
| DORA (EU Digital Operational Resilience Act) | 27 | Supported |
| ISO 27001 (Annex A 2022) | 16 | Supported |
| AI Act (EU Artificial Intelligence Act) | 19 | Supported |
| GDPR | — | Coming soon |
| NIS2 | — | Coming soon |

## CLI Reference

```bash
# Scan with options
grc scan .                              # All 3 regulations
grc scan . --regulation DORA            # Single regulation
grc scan src/ --extensions .py,.yaml    # Filter by file type
grc scan . --output report.json         # Save report
grc scan . --format json                # json | markdown | text
grc scan . --fail-under 80             # CI/CD quality gate (exit 1 if below)

# Evidence tracking
grc evidence init                       # Create evidence.db
grc evidence list                       # Show recorded evidence
grc evidence export --format json       # Export for auditors

# Inspect patterns
grc patterns list                       # All patterns
grc patterns list --regulation DORA     # Filter by regulation
grc patterns show DORA:Article_9        # Detail for one control
```

## Python API

```python
from grc_engine import scan, Score

# One-liner: scan and get scores
result = scan("/path/to/code")
print(result.scores)
# {"DORA": Score(pct=72.0, matched=5, total=7),
#  "ISO 27001": Score(pct=45.0, matched=3, total=6)}

# Per-regulation scan
result = scan("/path/to/code", regulation="DORA")
print(result.gaps)          # [Gap(control_id="DORA:Article_9", ...)]
print(result.to_json())     # Full JSON report
print(result.to_markdown()) # Markdown for docs/PRs

# Evidence store (optional, for tracking over time)
from grc_engine.evidence import EvidenceStore

store = EvidenceStore("./evidence.db")
store.record(result)
```

## How It Works

grc-engine scans your source code with 62 regex patterns that detect compliance-relevant constructs:

- Risk management frameworks, incident response procedures
- Authentication mechanisms, access controls, encryption
- CI/CD pipelines, code review enforcement, vulnerability scanning
- AI model governance, bias detection, audit logging

Each pattern maps to a specific regulatory control (e.g., `DORA:Article_9`). The scoring engine calculates per-regulation compliance percentages using a weighted model (70% completeness + 30% critical control coverage).

## License

MIT
