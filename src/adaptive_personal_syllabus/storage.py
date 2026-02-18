"""SQLite storage layer for corpus, planning, hooks, and ledger data."""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


DEFAULT_DATA_DIR = Path.home() / ".adaptive-syllabus"
DEFAULT_DB_PATH = DEFAULT_DATA_DIR / "adaptive_syllabus.db"
DEFAULT_PROFILE_PATH = DEFAULT_DATA_DIR / "profile.json"


def utcnow_iso() -> str:
    """UTC timestamp in ISO-8601 format."""
    return datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat()


class Storage:
    """Small SQLite wrapper with methods used by CLI and services."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = Path(db_path or DEFAULT_DB_PATH).expanduser().resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize_schema()

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def initialize_schema(self) -> None:
        """Create database schema if it does not exist."""
        with self.connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    canonical_path TEXT NOT NULL,
                    rel_path TEXT NOT NULL,
                    sha256 TEXT NOT NULL,
                    bytes INTEGER NOT NULL,
                    lines INTEGER NOT NULL,
                    mime TEXT NOT NULL,
                    family TEXT NOT NULL,
                    ingested_at TEXT NOT NULL
                );
                CREATE UNIQUE INDEX IF NOT EXISTS idx_documents_canonical_path
                    ON documents(canonical_path);
                CREATE INDEX IF NOT EXISTS idx_documents_sha256
                    ON documents(sha256);

                CREATE TABLE IF NOT EXISTS document_aliases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    alias_path TEXT NOT NULL,
                    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_document_aliases_document_id
                    ON document_aliases(document_id);

                CREATE TABLE IF NOT EXISTS document_chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    heading_path TEXT NOT NULL,
                    text TEXT NOT NULL,
                    token_estimate INTEGER NOT NULL,
                    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id
                    ON document_chunks(document_id);

                CREATE TABLE IF NOT EXISTS profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    level TEXT NOT NULL,
                    goals_json TEXT NOT NULL,
                    context_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    profile_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    total_hours REAL NOT NULL,
                    module_count INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS plan_modules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plan_id INTEGER NOT NULL,
                    seq INTEGER NOT NULL,
                    module_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    organ TEXT NOT NULL,
                    difficulty TEXT NOT NULL,
                    readings_json TEXT NOT NULL,
                    questions_json TEXT NOT NULL,
                    estimated_hours REAL NOT NULL,
                    FOREIGN KEY(plan_id) REFERENCES plans(id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_plan_modules_plan_id
                    ON plan_modules(plan_id);

                CREATE TABLE IF NOT EXISTS hook_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plan_id INTEGER,
                    hook_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    output_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(plan_id) REFERENCES plans(id) ON DELETE SET NULL
                );

                CREATE TABLE IF NOT EXISTS ledger_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prev_hash TEXT NOT NULL,
                    event_hash TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_ledger_events_id
                    ON ledger_events(id);

                CREATE TABLE IF NOT EXISTS snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_name TEXT NOT NULL,
                    root_path TEXT NOT NULL,
                    doc_count INTEGER NOT NULL,
                    unique_payload_count INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    def reset_corpus(self) -> None:
        """Clear corpus tables before re-ingestion."""
        with self.connection() as conn:
            conn.execute("DELETE FROM document_chunks")
            conn.execute("DELETE FROM document_aliases")
            conn.execute("DELETE FROM documents")

    def insert_snapshot(
        self,
        snapshot_name: str,
        root_path: str,
        doc_count: int,
        unique_payload_count: int,
    ) -> int:
        created_at = utcnow_iso()
        with self.connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO snapshots(snapshot_name, root_path, doc_count, unique_payload_count, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (snapshot_name, root_path, doc_count, unique_payload_count, created_at),
            )
            return int(cur.lastrowid)

    def latest_snapshot(self) -> dict[str, Any] | None:
        with self.connection() as conn:
            row = conn.execute(
                "SELECT * FROM snapshots ORDER BY id DESC LIMIT 1"
            ).fetchone()
        return dict(row) if row else None

    def insert_document(
        self,
        canonical_path: str,
        rel_path: str,
        sha256: str,
        size_bytes: int,
        lines: int,
        mime: str,
        family: str,
        ingested_at: str,
    ) -> int:
        with self.connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO documents(canonical_path, rel_path, sha256, bytes, lines, mime, family, ingested_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (canonical_path, rel_path, sha256, size_bytes, lines, mime, family, ingested_at),
            )
            return int(cur.lastrowid)

    def insert_alias(self, document_id: int, alias_path: str) -> None:
        with self.connection() as conn:
            conn.execute(
                "INSERT INTO document_aliases(document_id, alias_path) VALUES (?, ?)",
                (document_id, alias_path),
            )

    def insert_chunk(
        self,
        document_id: int,
        chunk_index: int,
        heading_path: str,
        text: str,
        token_estimate: int,
    ) -> None:
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO document_chunks(document_id, chunk_index, heading_path, text, token_estimate)
                VALUES (?, ?, ?, ?, ?)
                """,
                (document_id, chunk_index, heading_path, text, token_estimate),
            )

    def corpus_stats(self) -> dict[str, Any]:
        """Stable JSON schema for corpus statistics."""
        with self.connection() as conn:
            doc_count = int(conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0])
            alias_count = int(conn.execute("SELECT COUNT(*) FROM document_aliases").fetchone()[0])
            chunk_count = int(conn.execute("SELECT COUNT(*) FROM document_chunks").fetchone()[0])
            total_bytes = int(
                conn.execute("SELECT COALESCE(SUM(bytes), 0) FROM documents").fetchone()[0]
            )
            by_family_rows = conn.execute(
                "SELECT family, COUNT(*) AS n FROM documents GROUP BY family ORDER BY family"
            ).fetchall()
            latest_snapshot = conn.execute(
                "SELECT * FROM snapshots ORDER BY id DESC LIMIT 1"
            ).fetchone()
            ledger_events = int(conn.execute("SELECT COUNT(*) FROM ledger_events").fetchone()[0])

        family_breakdown = {str(row["family"]): int(row["n"]) for row in by_family_rows}
        return {
            "schema_version": "1.0",
            "document_count": doc_count,
            "alias_count": alias_count,
            "chunk_count": chunk_count,
            "total_bytes": total_bytes,
            "family_breakdown": family_breakdown,
            "latest_snapshot": dict(latest_snapshot) if latest_snapshot else None,
            "ledger_event_count": ledger_events,
        }

    def list_documents(self, limit: int | None = None) -> list[dict[str, Any]]:
        query = "SELECT id, canonical_path, rel_path, family, sha256 FROM documents ORDER BY canonical_path"
        params: tuple[Any, ...] = ()
        if limit is not None:
            query += " LIMIT ?"
            params = (limit,)
        with self.connection() as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def insert_profile(
        self,
        name: str,
        level: str,
        goals: list[str],
        context: dict[str, Any],
    ) -> int:
        created_at = utcnow_iso()
        with self.connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO profiles(name, level, goals_json, context_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name, level, json.dumps(goals), json.dumps(context), created_at),
            )
            return int(cur.lastrowid)

    def insert_plan(
        self,
        profile_id: int,
        title: str,
        total_hours: float,
        module_count: int,
    ) -> int:
        created_at = utcnow_iso()
        with self.connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO plans(profile_id, title, total_hours, module_count, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (profile_id, title, total_hours, module_count, created_at),
            )
            return int(cur.lastrowid)

    def insert_plan_module(
        self,
        plan_id: int,
        seq: int,
        module_id: str,
        title: str,
        organ: str,
        difficulty: str,
        readings: list[str],
        questions: list[str],
        estimated_hours: float,
    ) -> int:
        with self.connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO plan_modules(
                    plan_id, seq, module_id, title, organ, difficulty, readings_json, questions_json,
                    estimated_hours
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    plan_id,
                    seq,
                    module_id,
                    title,
                    organ,
                    difficulty,
                    json.dumps(readings),
                    json.dumps(questions),
                    estimated_hours,
                ),
            )
            return int(cur.lastrowid)

    def insert_hook_run(
        self,
        plan_id: int | None,
        hook_name: str,
        status: str,
        output: dict[str, Any],
    ) -> int:
        created_at = utcnow_iso()
        with self.connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO hook_runs(plan_id, hook_name, status, output_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (plan_id, hook_name, status, json.dumps(output), created_at),
            )
            return int(cur.lastrowid)

    def last_ledger_hash(self) -> str:
        with self.connection() as conn:
            row = conn.execute(
                "SELECT event_hash FROM ledger_events ORDER BY id DESC LIMIT 1"
            ).fetchone()
        return str(row["event_hash"]) if row else ""

    def append_ledger_event(
        self,
        prev_hash: str,
        event_hash: str,
        event_type: str,
        payload: dict[str, Any],
        created_at: str,
    ) -> int:
        with self.connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO ledger_events(prev_hash, event_hash, event_type, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (prev_hash, event_hash, event_type, json.dumps(payload, sort_keys=True), created_at),
            )
            return int(cur.lastrowid)

    def iter_ledger_events(self) -> list[dict[str, Any]]:
        with self.connection() as conn:
            rows = conn.execute("SELECT * FROM ledger_events ORDER BY id ASC").fetchall()
        return [dict(r) for r in rows]
