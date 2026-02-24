# CLAUDE.md — adaptive-personal-syllabus

**ORGAN VI** (Community) · `organvm-vi-koinonia/adaptive-personal-syllabus`
**Status:** ACTIVE · **Branch:** `main`

## What This Repo Is

AI-personalized education system with multi-module curriculum spanning OS development, algorithms, DSLs, and mixed reality. Features Wings multi-artifact framework.

## Stack

**Languages:** Python
**Build:** Python (pip/setuptools)
**Testing:** pytest (likely)

## Directory Structure

```
📁 .github/
📁 docs/
    Context-capture-and-analysis.md
    OnUpAway-Syllabus.md.md
    README.md
    adr
    aiChatsThread
    narrative-workbook
    seed.yaml
    source-materials
    syllabusEVOLUTION
    transcript-jf-ap-trading-cards.txt
📁 src/
    adaptive_personal_syllabus
📁 tests/
    __init__.py
    test_core.py
  CHANGELOG.md
  LICENSE
  README.md
  pyproject.toml
  seed.yaml
```

## Key Files

- `README.md` — Project documentation
- `pyproject.toml` — Python project config
- `seed.yaml` — ORGANVM orchestration metadata
- `src/` — Main source code
- `tests/` — Test suite

## Development

```bash
pip install -e .    # Install in development mode
pytest              # Run tests
```

## ORGANVM Context

This repository is part of the **ORGANVM** eight-organ creative-institutional system.
It belongs to **ORGAN VI (Community)** under the `organvm-vi-koinonia` GitHub organization.

**Registry:** [`registry-v2.json`](https://github.com/meta-organvm/organvm-corpvs-testamentvm/blob/main/registry-v2.json)
**Corpus:** [`organvm-corpvs-testamentvm`](https://github.com/meta-organvm/organvm-corpvs-testamentvm)

<!-- ORGANVM:AUTO:START -->
## System Context (auto-generated — do not edit)

**Organ:** ORGAN-VI (Community) | **Tier:** standard | **Status:** CANDIDATE
**Org:** `organvm-vi-koinonia` | **Repo:** `adaptive-personal-syllabus`

### Edges
- **Produces** → `learning_path`: Personalized learning paths based on organ interests and difficulty level
- **Consumes** ← `koinonia-db`: Shared database models, taxonomy, and reading data

### Siblings in Community
`community-hub` (flagship), `koinonia-db`, `salon-archive`, `reading-group-curriculum`, `.github`

### Governance
- Community infrastructure layer. Consumes from ORGAN-I, II, III. No back-edges.

*Last synced: 2026-02-24T12:00:00Z*
<!-- ORGANVM:AUTO:END -->
