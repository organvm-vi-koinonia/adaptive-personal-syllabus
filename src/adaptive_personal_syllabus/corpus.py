"""Corpus ingestion and document chunking utilities."""
from __future__ import annotations

import csv
import hashlib
import json
import mimetypes
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from .ledger import Ledger
from .models import CorpusSnapshot
from .storage import Storage, utcnow_iso


SUPPORTED_EXTENSIONS = {
    ".md",
    ".txt",
    ".yaml",
    ".yml",
    ".json",
    ".toml",
    ".csv",
    ".tsv",
    ".rst",
    ".pdf",
    ".docx",
}

TEXT_EXTENSIONS = {
    ".md",
    ".txt",
    ".yaml",
    ".yml",
    ".json",
    ".toml",
    ".csv",
    ".tsv",
    ".rst",
}

SKIP_DIRECTORIES = {".git", ".venv", ".pytest_cache", "__pycache__"}


FAMILY_BY_EXTENSION = {
    ".md": "markdown",
    ".txt": "text",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".toml": "toml",
    ".csv": "tabular",
    ".tsv": "tabular",
    ".rst": "text",
    ".pdf": "binary",
    ".docx": "binary",
}


@dataclass(frozen=True)
class CandidateDocument:
    path: Path
    rel_path: str
    extension: str
    sha256: str
    size_bytes: int
    lines: int
    mime: str
    family: str
    text: str | None


def _should_skip(path: Path, root: Path) -> bool:
    rel_parts = path.relative_to(root).parts
    return any(part in SKIP_DIRECTORIES for part in rel_parts)


def discover_documents(root: Path) -> list[Path]:
    """Discover supported document files under root, sorted deterministically."""
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if _should_skip(path, root):
            continue
        if path.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(path)
    return sorted(files, key=lambda p: str(p.relative_to(root)))


def _decode_text(data: bytes, path: Path) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"Unsupported encoding for {path}. Expected UTF-8.") from exc


def _validate_content(ext: str, text: str, path: Path) -> None:
    if ext == ".json":
        try:
            json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Malformed JSON file: {path}") from exc
    elif ext == ".toml":
        try:
            tomllib.loads(text)
        except tomllib.TOMLDecodeError as exc:
            raise ValueError(f"Malformed TOML file: {path}") from exc
    elif ext in {".csv", ".tsv"}:
        delimiter = "," if ext == ".csv" else "\t"
        reader = csv.reader(text.splitlines(), delimiter=delimiter)
        # Consume once to fail-fast on structural CSV errors.
        for _ in reader:
            break


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _family(ext: str) -> str:
    return FAMILY_BY_EXTENSION.get(ext, "unknown")


def _mime(path: Path) -> str:
    guessed, _ = mimetypes.guess_type(path.name)
    return guessed or "application/octet-stream"


def _count_lines(text: str | None, data: bytes) -> int:
    if text is None:
        if not data:
            return 0
        return data.count(b"\n") + 1
    if not text:
        return 0
    return text.count("\n") + 1


def _is_heading_line(line: str) -> tuple[int, str] | None:
    markdown_match = re.match(r"^\s{0,3}(#{1,6})\s+(.+?)\s*$", line)
    if markdown_match:
        level = len(markdown_match.group(1))
        heading = markdown_match.group(2).strip()
        return level, heading
    return None


def heading_aware_chunks(text: str) -> list[tuple[str, str]]:
    """Split text into heading-aware chunks with heading path labels."""
    if not text.strip():
        return []

    chunks: list[tuple[str, str]] = []
    heading_stack: list[str] = []
    buffer: list[str] = []

    def flush() -> None:
        chunk_text = "\n".join(buffer).strip()
        if chunk_text:
            heading_path = " / ".join(heading_stack)
            chunks.append((heading_path, chunk_text))
        buffer.clear()

    for line in text.splitlines():
        heading = _is_heading_line(line)
        if heading:
            flush()
            level, title = heading
            heading_stack[:] = heading_stack[: level - 1]
            heading_stack.append(title)
            continue
        buffer.append(line)

    flush()

    if not chunks:
        chunks.append(("", text.strip()))

    return chunks


class CorpusIngestor:
    """Ingest repository corpus, deduplicate by content hash, and persist chunks."""

    def __init__(self, storage: Storage, ledger: Ledger | None = None) -> None:
        self.storage = storage
        self.ledger = ledger

    def _build_candidate(self, root: Path, path: Path) -> CandidateDocument:
        data = path.read_bytes()
        ext = path.suffix.lower()
        text = None
        if ext in TEXT_EXTENSIONS:
            text = _decode_text(data, path)
            _validate_content(ext, text, path)

        rel_path = str(path.relative_to(root))
        return CandidateDocument(
            path=path,
            rel_path=rel_path,
            extension=ext,
            sha256=_sha256(data),
            size_bytes=len(data),
            lines=_count_lines(text, data),
            mime=_mime(path),
            family=_family(ext),
            text=text,
        )

    def ingest(self, root: Path, snapshot_name: str) -> CorpusSnapshot:
        root = root.expanduser().resolve()
        if not root.exists() or not root.is_dir():
            raise ValueError(f"Invalid root directory: {root}")

        paths = discover_documents(root)
        candidates = [self._build_candidate(root, p) for p in paths]

        by_hash: dict[str, list[CandidateDocument]] = {}
        for c in candidates:
            by_hash.setdefault(c.sha256, []).append(c)

        self.storage.reset_corpus()

        canonical_docs = 0
        alias_count = 0
        chunk_count = 0
        ingested_at = utcnow_iso()

        for sha in sorted(by_hash):
            group = sorted(by_hash[sha], key=lambda c: c.rel_path)
            canonical = group[0]
            canonical_docs += 1
            doc_id = self.storage.insert_document(
                canonical_path=str(canonical.path),
                rel_path=canonical.rel_path,
                sha256=canonical.sha256,
                size_bytes=canonical.size_bytes,
                lines=canonical.lines,
                mime=canonical.mime,
                family=canonical.family,
                ingested_at=ingested_at,
            )

            if canonical.text is not None:
                for idx, (heading_path, chunk_text) in enumerate(heading_aware_chunks(canonical.text)):
                    token_estimate = len(chunk_text.split())
                    self.storage.insert_chunk(
                        document_id=doc_id,
                        chunk_index=idx,
                        heading_path=heading_path,
                        text=chunk_text,
                        token_estimate=token_estimate,
                    )
                    chunk_count += 1

            for alias in group[1:]:
                self.storage.insert_alias(document_id=doc_id, alias_path=str(alias.path))
                alias_count += 1

        self.storage.insert_snapshot(
            snapshot_name=snapshot_name,
            root_path=str(root),
            doc_count=len(candidates),
            unique_payload_count=len(by_hash),
        )
        latest = self.storage.latest_snapshot()
        if latest is None:
            raise RuntimeError("Snapshot write failed")

        if self.ledger is not None:
            self.ledger.append(
                "corpus.ingest",
                {
                    "snapshot_name": snapshot_name,
                    "root_path": str(root),
                    "doc_count": len(candidates),
                    "unique_payload_count": len(by_hash),
                    "canonical_document_count": canonical_docs,
                    "alias_count": alias_count,
                    "chunk_count": chunk_count,
                },
            )

        return CorpusSnapshot(
            snapshot_name=str(latest["snapshot_name"]),
            root_path=str(latest["root_path"]),
            doc_count=int(latest["doc_count"]),
            unique_payload_count=int(latest["unique_payload_count"]),
            created_at=str(latest["created_at"]),
        )
