# ADR-001: Initial Architecture and Technology Choices

## Status

Accepted

## Date

2026-02-13

## Context

`adaptive-personal-syllabus` is a Python-based project within ORGAN-VI (Koinonia) of the organvm eight-organ creative-institutional system. The project needed a technology foundation that balances rapid prototyping with long-term maintainability.

## Decision

We chose Python as the primary implementation language. Key architectural choices:
- **Language**: Python — selected for ecosystem fit and domain requirements
- **CI/CD**: GitHub Actions with graceful degradation (tests, linting, type checking)
- **Documentation**: Portfolio-quality README targeting grant reviewers and hiring managers
- **Governance**: Follows ORGAN-IV orchestration rules; no back-edges in dependency graph

## Consequences

### Positive

- Consistent with organvm system-wide conventions
- CI pipeline catches regressions early with continue-on-error for non-critical checks
- Documentation-first approach ensures discoverability and portfolio value

### Negative

- Python ecosystem fragmentation requires flexible dependency detection in CI
- Portfolio-quality documentation requires ongoing maintenance

## References

- Part of the [organvm eight-organ system](https://github.com/meta-organvm)
- Organ: ORGAN-VI (Koinonia)
