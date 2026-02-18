"""Tests for ledger append and verification."""

from __future__ import annotations

from pathlib import Path

from adaptive_personal_syllabus.ledger import Ledger
from adaptive_personal_syllabus.storage import Storage


def test_ledger_verify_success(tmp_path: Path) -> None:
    storage = Storage(tmp_path / "ok.db")
    ledger = Ledger(storage)

    ledger.append("event.a", {"x": 1})
    ledger.append("event.b", {"y": 2})

    ok, errors, count = ledger.verify_chain()
    assert ok is True
    assert errors == []
    assert count == 2


def test_ledger_verify_detects_tamper(tmp_path: Path) -> None:
    storage = Storage(tmp_path / "tamper.db")
    ledger = Ledger(storage)

    ledger.append("event.a", {"x": 1})
    ledger.append("event.b", {"y": 2})

    with storage.connection() as conn:
        conn.execute("UPDATE ledger_events SET payload_json = ? WHERE id = 1", ('{"x":999}',))

    ok, errors, count = ledger.verify_chain()
    assert ok is False
    assert count == 2
    assert any("event_hash mismatch" in err for err in errors)
