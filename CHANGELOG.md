# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2026-02-17

### Added
- **AQUA COMMUNIS sprint** — CLI and DB generator test coverage
- `tests/test_db_generator.py` — 5 tests: URL normalization, passthrough, psycopg, empty taxonomy, data build
- `tests/test_cli.py` — 5 tests: version, text/json/md format, missing organs error
- Test count: 9 → 19 (+10)

## [0.3.0] - 2026-02-17

### Added
- `DatabaseSyllabusGenerator` — reads taxonomy/readings from Neon DB and persists generated paths
- Syllabus schema models: `LearnerProfileRow`, `LearningPathRow`, `LearningModuleRow`
- Database persistence for generated learning paths

## [0.2.0] - 2026-02-17

### Added

- `__main__.py` for `python -m adaptive_personal_syllabus` support
- `total_modules` field on LearnerProfile for accurate progress tracking

### Fixed

- Generator now filters readings per child topic instead of giving every child the same readings
- Progress percentage now based on actual module count (not arbitrary 10x multiplier)

## [0.1.1] - 2026-02-13

### Added

- CONVERGENCE Sprint: Full PRODUCTION promotion — CI/CD, prototype skeleton, ADRs, badge row
- Provenance materials deployed from local source archive

## [0.1.0] - 2026-02-13

### Added

- Initial public release as part of the organvm eight-organ system
- Core project structure and documentation
- README with portfolio-quality documentation

[Unreleased]: https://github.com/organvm-vi-koinonia/adaptive-personal-syllabus/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/organvm-vi-koinonia/adaptive-personal-syllabus/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/organvm-vi-koinonia/adaptive-personal-syllabus/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/organvm-vi-koinonia/adaptive-personal-syllabus/releases/tag/v0.1.0
