"""Deterministic docs-audit pipeline for ingest + suggestion/use-case tracking."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .corpus import CorpusIngestor, TEXT_EXTENSIONS, discover_documents
from .ledger import Ledger
from .storage import Storage, utcnow_iso


ACTIONABLE_MARKER = re.compile(r"actionable suggestions?\s*:?", re.IGNORECASE)
USE_CASE_PATTERN = re.compile(r"\buse[- ]cases?\b", re.IGNORECASE)
LEADING_ENUM_PATTERN = re.compile(r"^\s*(?:[-*•]\s+|\d+\.\s+)+")

ACTION_VERB_PATTERN = re.compile(
    (
        r"^(add|align|annotate|benchmark|break|build|clarify|create|define|design|develop|"
        r"document|ensure|expand|guide|implement|improve|include|integrate|introduce|link|"
        r"map|offer|optimi[sz]e|phase|plan|position|prioritize|provide|quantify|reference|"
        r"set|simplify|specify|tier|track)\b"
    ),
    re.IGNORECASE,
)


IMPLEMENTED_CAPABILITY_RULES: list[tuple[str, tuple[str, ...]]] = [
    (
        "corpus.ingest-and-dedup",
        (
            "ingest",
            "dedup",
            "snapshot",
            "chunk",
            "json schema",
            "schema validation",
            "yaml",
            "toml",
            "csv",
            "tsv",
        ),
    ),
    (
        "ledger.hash-chain-and-provenance",
        (
            "ledger",
            "hash",
            "cryptographic",
            "chainblockark",
            "provenance",
            "prompt logging",
            "logging hooks",
        ),
    ),
    (
        "profile-and-plan-generation",
        (
            "learner profile",
            "profile",
            "personalization",
            "goals",
            "context",
            "wings",
            "artifact descriptors",
        ),
    ),
    (
        "cli-interfaces-and-json-exports",
        (
            "cli command",
            "json export",
            "markdown export",
            "corpus stats",
            "ledger verify",
            "profile init",
            "plan generate",
        ),
    ),
    (
        "chamber-hook-extension-points",
        (
            "aaw",
            "chamber",
            "hook",
            "character node",
            "self_as_mirror",
            "lg4",
        ),
    ),
]


MILESTONE_RULES: list[tuple[str, tuple[str, ...]]] = [
    (
        "pedagogy-scaffolding",
        (
            "quiz",
            "exercise",
            "rubric",
            "assessment",
            "tutorial",
            "scaffold",
            "prerequisite",
            "primer",
            "troubleshooting",
            "faq",
        ),
    ),
    (
        "systems-kernel-runtime",
        (
            "kernel",
            "bootloader",
            "scheduler",
            "filesystem",
            "memory",
            "interrupt",
            "qemu",
            "driver",
            "microkernel",
            "eBPF".lower(),
        ),
    ),
    (
        "dsl-neural-symbolic-verification",
        (
            "dsl",
            "antlr",
            "parser",
            "interpreter",
            "grammar",
            "meta-circular",
            "z3",
            "smt",
            "symbolic",
            "neural",
        ),
    ),
    (
        "ui-xr-accessibility",
        (
            "ui",
            "ux",
            "audio",
            "video",
            "aria",
            "a11y",
            "accessibility",
            "mobile",
            "ar",
            "vr",
            "xr",
            "screen-reader",
        ),
    ),
    (
        "integration-observability-ci",
        (
            "integration",
            "roadmap",
            "milestone",
            "benchmark",
            "performance",
            "kpi",
            "metric",
            "ci",
            "cicd",
            "workflow",
            "recovery",
        ),
    ),
    (
        "wings-community-governance",
        (
            "academic",
            "business",
            "social",
            "community",
            "wiki",
            "web/blog",
            "grants",
            "governance",
            "public scholarship",
            "building in public",
        ),
    ),
]


@dataclass(frozen=True)
class ExtractedItem:
    text: str
    rel_path: str
    line: int


def _normalize_text(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"\*+", "", lowered)
    lowered = re.sub(r"\s+", " ", lowered).strip()
    lowered = re.sub(r"[^a-z0-9 ]+", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def _clean_text(text: str) -> str:
    cleaned = LEADING_ENUM_PATTERN.sub("", text.strip())
    cleaned = re.sub(r"\*\*", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .;:-")
    return cleaned.strip()


def _split_suggestion_blob(blob: str) -> list[str]:
    if not blob.strip():
        return []

    work = blob.replace("•", ";")
    work = ACTIONABLE_MARKER.sub("", work).strip()
    work = re.sub(r"\s+", " ", work)
    work = re.sub(r"\s+\d+\.\s+", " || ", f" {work} ").strip()
    work = work.replace(";", " || ")

    parts: list[str] = []
    for candidate in work.split("||"):
        cleaned = _clean_text(candidate)
        if cleaned:
            parts.append(cleaned)
    return parts


def _extract_items_from_text(text: str, rel_path: str) -> tuple[list[ExtractedItem], list[ExtractedItem]]:
    suggestions: list[ExtractedItem] = []
    use_cases: list[ExtractedItem] = []
    lines = text.splitlines()

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue

        if USE_CASE_PATTERN.search(stripped):
            cleaned_use_case = _clean_text(stripped)
            if cleaned_use_case:
                use_cases.append(ExtractedItem(cleaned_use_case, rel_path, i))

        marker_match = ACTIONABLE_MARKER.search(stripped)
        if marker_match:
            inline = stripped[marker_match.end():].strip(" :-")
            for text_item in _split_suggestion_blob(inline):
                suggestions.append(ExtractedItem(text_item, rel_path, i))

            lookahead = i
            while lookahead < len(lines):
                nxt_raw = lines[lookahead]
                nxt = nxt_raw.strip()
                if not nxt:
                    if suggestions:
                        break
                    lookahead += 1
                    continue
                if not re.match(r"^\s*(?:[-*•]|\d+\.)\s+", nxt_raw):
                    break
                for text_item in _split_suggestion_blob(nxt):
                    suggestions.append(ExtractedItem(text_item, rel_path, lookahead + 1))
                lookahead += 1
            continue

        if re.match(r"^\s*(?:[-*•]|\d+\.)\s+", line):
            bullet_text = _clean_text(stripped)
            if bullet_text and ACTION_VERB_PATTERN.search(bullet_text):
                suggestions.append(ExtractedItem(bullet_text, rel_path, i))

    return suggestions, use_cases


def _classify_suggestion(text: str) -> tuple[str, list[str], str | None]:
    lowered = text.lower()
    tags = [
        tag
        for tag, keywords in IMPLEMENTED_CAPABILITY_RULES
        if any(keyword in lowered for keyword in keywords)
    ]
    if tags:
        return "implemented", sorted(tags), None

    for milestone, keywords in MILESTONE_RULES:
        if any(keyword in lowered for keyword in keywords):
            return "planned", [], milestone
    return "planned", [], "general-backlog"


def _stable_item_id(prefix: str, text: str) -> str:
    digest = hashlib.sha256(_normalize_text(text).encode("utf-8")).hexdigest()[:12]
    return f"{prefix}-{digest}"


def _aggregate_items(items: list[ExtractedItem], prefix: str) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for item in items:
        normalized = _normalize_text(item.text)
        if len(normalized) < 5:
            continue
        if normalized not in grouped:
            grouped[normalized] = {
                "id": _stable_item_id(prefix, item.text),
                "text": item.text,
                "source_refs": [],
            }
        grouped[normalized]["source_refs"].append({"rel_path": item.rel_path, "line": item.line})

    out: list[dict[str, Any]] = []
    for normalized, item in grouped.items():
        refs = sorted(
            {(ref["rel_path"], ref["line"]) for ref in item["source_refs"]},
            key=lambda pair: (pair[0], pair[1]),
        )
        collapsed_refs = [{"rel_path": rel_path, "line": line} for rel_path, line in refs]
        status, impl_tags, milestone = _classify_suggestion(item["text"])
        out_item = {
            "id": item["id"],
            "normalized_text": normalized,
            "text": item["text"],
            "status": status,
            "implementation_tags": impl_tags,
            "planned_milestone": milestone,
            "source_refs": collapsed_refs,
        }
        out.append(out_item)

    return sorted(out, key=lambda entry: (entry["status"], entry["text"].lower()))


def _path_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class DocsAuditService:
    """Generate deterministic docs-audit reports from repository docs content."""

    def __init__(self, storage: Storage, ledger: Ledger) -> None:
        self.storage = storage
        self.ledger = ledger

    def audit(
        self,
        *,
        root: Path,
        snapshot_name: str,
        exclude_paths: set[Path] | None = None,
    ) -> dict[str, Any]:
        root = root.expanduser().resolve()
        excluded = {p.expanduser().resolve() for p in (exclude_paths or set())}
        ingestor = CorpusIngestor(self.storage, self.ledger)
        snapshot = ingestor.ingest(root=root, snapshot_name=snapshot_name, exclude_paths=excluded)

        paths = [path for path in discover_documents(root) if path.resolve() not in excluded]
        file_manifest: list[dict[str, Any]] = []
        by_sha: dict[str, list[Path]] = {}
        for path in paths:
            sha = _path_sha256(path)
            by_sha.setdefault(sha, []).append(path)

        for sha, hash_paths in sorted(by_sha.items(), key=lambda pair: (pair[0], str(pair[1][0]))):
            canonical = sorted(hash_paths, key=lambda p: str(p.relative_to(root)))[0]
            canonical_rel = str(canonical.relative_to(root))
            for path in sorted(hash_paths, key=lambda p: str(p.relative_to(root))):
                rel_path = str(path.relative_to(root))
                file_manifest.append(
                    {
                        "rel_path": rel_path,
                        "canonical_rel_path": canonical_rel,
                        "sha256": sha,
                        "size_bytes": path.stat().st_size,
                        "extension": path.suffix.lower(),
                        "is_duplicate_payload": rel_path != canonical_rel,
                    }
                )

        extracted_suggestions: list[ExtractedItem] = []
        extracted_use_cases: list[ExtractedItem] = []
        for sha in sorted(by_sha):
            canonical = sorted(by_sha[sha], key=lambda p: str(p.relative_to(root)))[0]
            if canonical.suffix.lower() not in TEXT_EXTENSIONS:
                continue
            text = canonical.read_text(encoding="utf-8")
            rel_path = str(canonical.relative_to(root))
            suggestions, use_cases = _extract_items_from_text(text, rel_path)
            extracted_suggestions.extend(suggestions)
            extracted_use_cases.extend(use_cases)

        suggestions = _aggregate_items(extracted_suggestions, prefix="feat")
        use_cases = _aggregate_items(extracted_use_cases, prefix="usecase")

        implemented_count = sum(1 for item in suggestions if item["status"] == "implemented")
        planned_count = sum(1 for item in suggestions if item["status"] == "planned")

        snapshot_stats = self.storage.corpus_stats(snapshot_id=snapshot.snapshot_id)
        all_files_ingested = int(snapshot_stats["snapshot"]["doc_count"]) == len(file_manifest)

        report = {
            "schema_version": "1.0",
            "generated_at": utcnow_iso(),
            "root_path": str(root),
            "snapshot": {
                "snapshot_id": snapshot.snapshot_id,
                "snapshot_name": snapshot.snapshot_name,
                "doc_count": snapshot.doc_count,
                "unique_payload_count": snapshot.unique_payload_count,
                "created_at": snapshot.created_at,
            },
            "ingest_verification": {
                "expected_file_count": len(file_manifest),
                "snapshot_doc_count": int(snapshot_stats["snapshot"]["doc_count"]),
                "all_files_ingested": all_files_ingested,
            },
            "files": sorted(file_manifest, key=lambda item: item["rel_path"]),
            "suggestions": {
                "count": len(suggestions),
                "implemented_count": implemented_count,
                "planned_count": planned_count,
                "items": suggestions,
            },
            "use_cases": {
                "count": len(use_cases),
                "items": use_cases,
            },
        }

        self.ledger.append(
            "docs.audit",
            {
                "root_path": str(root),
                "snapshot_id": snapshot.snapshot_id,
                "snapshot_name": snapshot.snapshot_name,
                "file_count": len(file_manifest),
                "suggestion_count": len(suggestions),
                "implemented_count": implemented_count,
                "planned_count": planned_count,
                "use_case_count": len(use_cases),
            },
        )
        return report


def render_audit_markdown(report: dict[str, Any]) -> str:
    """Render a concise markdown roadmap for suggestions and use-cases."""
    snapshot = report["snapshot"]
    verify = report["ingest_verification"]
    suggestion_items = report["suggestions"]["items"]

    lines = [
        "# Docs Audit Report",
        "",
        f"- Generated at: `{report['generated_at']}`",
        f"- Root: `{report['root_path']}`",
        f"- Snapshot: `{snapshot['snapshot_name']}` (id={snapshot['snapshot_id']})",
        f"- Files discovered: `{verify['expected_file_count']}`",
        f"- Files ingested: `{verify['snapshot_doc_count']}`",
        f"- Ingest complete: `{verify['all_files_ingested']}`",
        "",
        "## Suggestions Summary",
        "",
        f"- Total suggestions: `{report['suggestions']['count']}`",
        f"- Implemented: `{report['suggestions']['implemented_count']}`",
        f"- Planned: `{report['suggestions']['planned_count']}`",
        "",
        "## Planned Milestones",
        "",
    ]

    by_milestone: dict[str, list[dict[str, Any]]] = {}
    for item in suggestion_items:
        if item["status"] != "planned":
            continue
        milestone = item["planned_milestone"] or "general-backlog"
        by_milestone.setdefault(milestone, []).append(item)

    if not by_milestone:
        lines.append("- None")
    else:
        for milestone in sorted(by_milestone):
            lines.append(f"### {milestone}")
            for item in sorted(by_milestone[milestone], key=lambda entry: entry["text"].lower()):
                source = item["source_refs"][0]
                lines.append(f"- `{item['id']}` {item['text']} ({source['rel_path']}:{source['line']})")
            lines.append("")

    lines.extend(
        [
            "## Implemented Coverage",
            "",
        ]
    )

    implemented = [item for item in suggestion_items if item["status"] == "implemented"]
    if not implemented:
        lines.append("- None")
    else:
        for item in sorted(implemented, key=lambda entry: entry["text"].lower()):
            tags = ", ".join(item["implementation_tags"]) or "n/a"
            source = item["source_refs"][0]
            lines.append(f"- `{item['id']}` {item['text']} [{tags}] ({source['rel_path']}:{source['line']})")

    lines.extend(
        [
            "",
            "## Use-Cases",
            "",
            f"- Total use-case mentions: `{report['use_cases']['count']}`",
        ]
    )

    for item in report["use_cases"]["items"]:
        source = item["source_refs"][0]
        lines.append(f"- `{item['id']}` {item['text']} ({source['rel_path']}:{source['line']})")

    return "\n".join(lines) + "\n"


def write_report(path: Path, content: str | dict[str, Any]) -> None:
    """Write markdown or JSON report content to disk."""
    path = path.expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(content, str):
        path.write_text(content, encoding="utf-8")
        return
    path.write_text(json.dumps(content, indent=2), encoding="utf-8")
