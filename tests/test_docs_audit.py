"""Tests for docs audit ingestion, extraction, and classification."""

from __future__ import annotations

from pathlib import Path

from adaptive_personal_syllabus.docs_audit import DocsAuditService
from adaptive_personal_syllabus.ledger import Ledger
from adaptive_personal_syllabus.storage import Storage


def _build_docs(root: Path) -> None:
    (root / "a.md").write_text(
        (
            "# Critique\n"
            "- **Actionable Suggestions**: 1. Add cryptographic hashing protocols to the SOP for prompt "
            "logging. 2. Add step-by-step exercises with incremental milestones.\n"
            "- Use Case: Link repository metadata to ChainBlockARK logs.\n"
        ),
        encoding="utf-8",
    )
    # Duplicate payload on purpose.
    (root / "b.md").write_text((root / "a.md").read_text(encoding="utf-8"), encoding="utf-8")
    (root / "c.txt").write_text(
        "- Actionable Suggestions: Define CI pipelines for kernel builds.\n",
        encoding="utf-8",
    )


def test_docs_audit_ingests_every_file_and_tracks_status(tmp_path: Path) -> None:
    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    _build_docs(docs_root)

    storage = Storage(tmp_path / "audit.db")
    ledger = Ledger(storage)
    report = DocsAuditService(storage=storage, ledger=ledger).audit(
        root=docs_root,
        snapshot_name="docs-test",
    )

    assert report["ingest_verification"]["all_files_ingested"] is True
    assert report["ingest_verification"]["expected_file_count"] == 3
    assert report["snapshot"]["doc_count"] == 3
    assert len(report["files"]) == 3

    duplicate = next(item for item in report["files"] if item["rel_path"] == "b.md")
    assert duplicate["is_duplicate_payload"] is True

    by_text = {item["text"]: item for item in report["suggestions"]["items"]}
    hashing_item = by_text["Add cryptographic hashing protocols to the SOP for prompt logging"]
    exercises_item = by_text["Add step-by-step exercises with incremental milestones"]
    ci_item = by_text["Define CI pipelines for kernel builds"]

    assert hashing_item["status"] == "implemented"
    assert "ledger.hash-chain-and-provenance" in hashing_item["implementation_tags"]
    assert exercises_item["status"] == "planned"
    assert exercises_item["planned_milestone"] == "pedagogy-scaffolding"
    assert ci_item["status"] == "planned"
    assert ci_item["planned_milestone"] == "systems-kernel-runtime"

    assert report["use_cases"]["count"] >= 1
