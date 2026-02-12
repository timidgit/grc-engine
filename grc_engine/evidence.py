"""SQLite evidence store for tracking compliance over time."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from grc_engine import ScanResult

_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS evidence (
    evidence_id  TEXT PRIMARY KEY,
    control_id   TEXT NOT NULL,
    source       TEXT NOT NULL,
    file_path    TEXT,
    content_hash TEXT NOT NULL,
    status       TEXT NOT NULL CHECK(status IN ('pass','fail','partial','stale')),
    details      TEXT,
    created_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_evidence_control ON evidence(control_id);
CREATE INDEX IF NOT EXISTS idx_evidence_status  ON evidence(status);
CREATE INDEX IF NOT EXISTS idx_evidence_created ON evidence(created_at);
"""


class EvidenceStore:
    """Zero-config SQLite evidence store.

    Auto-creates the database on first use. No external dependencies.
    """

    def __init__(self, db_path: str | Path = "./evidence.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.executescript(_CREATE_SQL)

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def record(self, result: ScanResult) -> list[str]:
        """Record a ScanResult to the evidence store.

        Args:
            result: A ScanResult from grc_engine.scan().

        Returns:
            List of evidence IDs created.
        """
        ids = []
        for match in result.matches:
            eid = self.record_evidence(
                control_id=match.control_id,
                source="grc-engine-scan",
                file_path=match.file,
                status="pass",
                details={
                    "pattern_id": match.pattern_id,
                    "label": match.label,
                    "match_count": match.match_count,
                },
            )
            ids.append(eid)
        return ids

    def record_evidence(
        self,
        control_id: str,
        source: str,
        file_path: Optional[str] = None,
        content_hash: Optional[str] = None,
        status: str = "pass",
        details: Optional[dict] = None,
    ) -> str:
        """Record a piece of compliance evidence. Returns the evidence_id."""
        evidence_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        if content_hash is None:
            raw = f"{control_id}:{source}:{file_path}:{now}"
            content_hash = hashlib.sha256(raw.encode()).hexdigest()

        with self._conn() as conn:
            conn.execute(
                """INSERT INTO evidence
                   (evidence_id, control_id, source, file_path,
                    content_hash, status, details, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    evidence_id,
                    control_id,
                    source,
                    file_path,
                    content_hash,
                    status,
                    json.dumps(details) if details else None,
                    now,
                ),
            )
        return evidence_id

    def get_evidence(
        self,
        control_id: Optional[str] = None,
        since: Optional[str] = None,
        limit: int = 1000,
    ) -> list[dict]:
        """Retrieve evidence records."""
        with self._conn() as conn:
            query = "SELECT * FROM evidence"
            params: list = []
            conditions = []

            if control_id:
                conditions.append("control_id = ?")
                params.append(control_id)
            if since:
                conditions.append("created_at >= ?")
                params.append(since)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def get_coverage_summary(self, regulation: Optional[str] = None) -> dict:
        """Return coverage summary: controls with evidence, pass/fail breakdown."""
        with self._conn() as conn:
            if regulation:
                like = f"{regulation}%"
                rows = conn.execute(
                    """SELECT control_id, status, COUNT(*) as cnt
                       FROM evidence WHERE control_id LIKE ?
                       GROUP BY control_id, status""",
                    (like,),
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT control_id, status, COUNT(*) as cnt
                       FROM evidence GROUP BY control_id, status"""
                ).fetchall()

        controls: dict[str, dict] = {}
        for r in rows:
            r = dict(r)
            cid = r["control_id"]
            if cid not in controls:
                controls[cid] = {"pass": 0, "fail": 0, "partial": 0, "stale": 0}
            controls[cid][r["status"]] += r["cnt"]

        total = len(controls)
        passing = sum(
            1 for c in controls.values() if c["pass"] > 0 and c["fail"] == 0
        )

        return {
            "total_controls_with_evidence": total,
            "passing": passing,
            "coverage_pct": round(passing / total * 100, 1) if total else 0.0,
        }

    def history(self, regulation: Optional[str] = None, days: int = 30) -> list[dict]:
        """Get scan history for the last N days."""
        since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        evidence = self.get_evidence(since=since)
        if regulation:
            evidence = [
                e for e in evidence if e["control_id"].startswith(regulation)
            ]
        return evidence
