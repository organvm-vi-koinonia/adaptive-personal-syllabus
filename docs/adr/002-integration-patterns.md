# ADR-002: Cross-Organ Integration and Dependency Patterns

## Status

Accepted

## Date

2026-02-13

## Context

The organvm system enforces a strict dependency flow: ORGAN-I (Theory) feeds into ORGAN-II (Art), which feeds into ORGAN-III (Commerce). ORGAN-IV (Orchestration) governs all organs. No back-edges are permitted. `adaptive-personal-syllabus` must define its integration points within this constraint.

## Decision

This repository participates in the cross-organ dependency graph as follows:
- **Upstream dependencies**: Defined in `registry-v2.json` under the `dependencies` field
- **Integration pattern**: Python package imports via pip
- **Communication**: Asynchronous — repos communicate through versioned releases and registry state

## Consequences

### Positive

- No circular dependencies — the dependency graph is a DAG validated by CI
- Loose coupling allows independent development and deployment

### Negative

- Cross-organ changes require coordinated registry updates
- Promotion gates may slow rapid iteration during prototyping

## References

- Dependency validation: `validate-dependencies.yml` in [orchestration-start-here](https://github.com/organvm-iv-taxis/orchestration-start-here)
- Organ: ORGAN-VI (Koinonia)
