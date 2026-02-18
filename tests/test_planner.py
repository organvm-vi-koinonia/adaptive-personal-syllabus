"""Tests for profile-aware planning."""

from __future__ import annotations

import json
from pathlib import Path

from adaptive_personal_syllabus.corpus import CorpusIngestor
from adaptive_personal_syllabus.ledger import Ledger
from adaptive_personal_syllabus.planner import Planner
from adaptive_personal_syllabus.storage import Storage


def _seed_dir(base: Path) -> Path:
    seed_dir = base / "seed"
    seed_dir.mkdir()
    (seed_dir / "taxonomy.json").write_text(
        json.dumps(
            {
                "nodes": [
                    {
                        "slug": "i-theoria",
                        "label": "Theoria",
                        "children": [
                            {"slug": "foundations", "label": "Foundations"},
                            {"slug": "abstractions", "label": "Abstractions"},
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (seed_dir / "reading_lists.json").write_text(
        json.dumps(
            {
                "entries": [
                    {
                        "title": "Intro to Theoria",
                        "organ_tags": ["i-theoria", "foundations"],
                        "difficulty": "beginner",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    return seed_dir


def _profile(path: Path) -> Path:
    profile_path = path / "profile.json"
    profile_path.write_text(
        json.dumps(
            {
                "name": "Planner Test",
                "organs_of_interest": ["I"],
                "level": "beginner",
                "goals": ["Build a recursive system"],
                "context": {"industry": "education"},
                "completed_modules": [],
            }
        ),
        encoding="utf-8",
    )
    return profile_path


def test_planner_generate_is_deterministic_for_same_profile_and_snapshot(tmp_path: Path) -> None:
    db_path = tmp_path / "planner.db"
    storage = Storage(db_path)
    ledger = Ledger(storage)

    corpus_root = tmp_path / "corpus"
    corpus_root.mkdir()
    (corpus_root / "doc.md").write_text("# Heading\nBody", encoding="utf-8")
    CorpusIngestor(storage, ledger).ingest(corpus_root, "snapshot-a")

    planner = Planner(storage=storage, ledger=ledger, seed_dir=_seed_dir(tmp_path))
    profile_path = _profile(tmp_path)

    plan_one = planner.generate(profile_path)
    plan_two = planner.generate(profile_path)

    assert plan_one["plan_id"] == plan_two["plan_id"]
    assert [m["module_id"] for m in plan_one["modules"]] == [
        m["module_id"] for m in plan_two["modules"]
    ]
    assert plan_one["modules"][0]["artifact_descriptors"]
    assert len(plan_one["modules"][0]["artifact_descriptors"]) == 8
    assert plan_one["modules"][0]["evidence"]
