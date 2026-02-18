"""CLI tests for docs audit command."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from adaptive_personal_syllabus.core import cli


def _build_docs(root: Path) -> None:
    (root / "sample.md").write_text(
        (
            "# Example\n"
            "- Actionable Suggestions: 1. Add benchmarks for ledger growth. "
            "2. Provide AR/VR setup primers.\n"
            "- Use Case: Demonstrate recursive planning for capstone integration.\n"
        ),
        encoding="utf-8",
    )


def test_cli_docs_audit_json_and_written_reports(tmp_path: Path) -> None:
    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    _build_docs(docs_root)

    db_path = tmp_path / "audit.db"
    output_dir = docs_root / "implementation"
    output_dir.mkdir()
    json_out = output_dir / "report.json"
    md_out = output_dir / "report.md"

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "docs",
            "audit",
            "--root",
            str(docs_root),
            "--snapshot",
            "docs-cli-test",
            "--format",
            "json",
            "--write-json",
            str(json_out),
            "--write-md",
            str(md_out),
            "--db-path",
            str(db_path),
        ],
    )
    assert result.exit_code == 0

    payload = json.loads(result.output)
    assert payload["snapshot"]["snapshot_name"] == "docs-cli-test"
    assert payload["ingest_verification"]["all_files_ingested"] is True
    # The docs command should exclude its own output files from ingestion scope.
    assert payload["ingest_verification"]["expected_file_count"] == 1
    assert json_out.exists()
    assert md_out.exists()
    assert "Docs Audit Report" in md_out.read_text(encoding="utf-8")


def test_cli_docs_execute_milestone_exports_plan(tmp_path: Path) -> None:
    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    _build_docs(docs_root)

    db_path = tmp_path / "audit.db"
    output_dir = docs_root / "implementation" / "milestones"
    output_dir.mkdir(parents=True)
    json_out = output_dir / "integration-plan.json"
    md_out = output_dir / "integration-plan.md"

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "docs",
            "execute-milestone",
            "--root",
            str(docs_root),
            "--snapshot",
            "docs-cli-exec",
            "--milestone",
            "integration-observability-ci",
            "--format",
            "json",
            "--write-json",
            str(json_out),
            "--write-md",
            str(md_out),
            "--db-path",
            str(db_path),
        ],
    )
    assert result.exit_code == 0

    payload = json.loads(result.output)
    assert payload["milestone"] == "integration-observability-ci"
    assert payload["selected_item_count"] >= 1
    assert json_out.exists()
    assert md_out.exists()
    assert "Milestone Execution Plan" in md_out.read_text(encoding="utf-8")
