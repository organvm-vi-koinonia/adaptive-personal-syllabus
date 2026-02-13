# ORG VI: Community (THE GARDEN)

## Role: Cultivation

Community governance, contribution frameworks, and cultivation protocols.

## Position in Metasystem

```
I (Origin) → II (Art) → III (Commerce) → V (Public Process) → [VI (Community)] → VII (Marketing)
                                                                    ↑ You are here
```

## Upstream / Downstream

- **Receives from:** ORG V (Public Process) via `community-approval` gate
- **Sends to:** ORG VII (Marketing) via `quality-threshold` gate
- **Orchestrated by:** ORG IV (Orchestration)

## Directory Structure

```
ORG-VI-community-staging/
├── seed.yaml                 # Automation contract
├── README.md                 # This file
├── governance-framework/     # Decision-making processes, voting
├── contribution-guides/      # How to contribute
├── salon-protocols/          # Community gathering formats
├── reading-lists/            # Curated resources
└── moderation-agents/        # Community health monitoring
```

## Purpose

This organ nurtures an engaged, self-governing community:

1. **Governance**: RFC process, voting mechanisms, decision frameworks
2. **Onboarding**: Clear paths from newcomer to active contributor
3. **Salons**: Regular community gatherings for discussion and creation
4. **Moderation**: Health monitoring and conflict resolution
5. **Curation**: Reading lists, resources, learning paths

## Automation Contract

AI agents may:
- Read and write to `contribution-guides/` and `reading-lists/`
- Monitor community health (via moderation agents)
- Assist with onboarding

AI agents may NOT:
- Modify `seed.yaml`
- Write to `governance-framework/` (requires human approval)
- Make governance decisions autonomously

## Gates

### Inbound Gate: `community-approval`
All changes affecting the community must:
- Publish an RFC document
- Observe 7-day comment period
- Address all blocking objections
- Meet vote threshold (if applicable)

### Outbound Gate: `quality-threshold`
Content for marketing must:
- Be reviewed by at least one peer
- Follow brand guidelines
- Have technical claims verified

## Moderation Agents

| Agent | Purpose |
|-------|---------|
| `health-monitor` | Monitors sentiment, flags issues |
| `onboarding-guide` | Assists new contributors |

## GitHub Organization

**Status:** TBD (staging)

Suggested options:
- New org: `reciprocal-continuity`
- Extend existing: `ivviiviivvi` (THE ALCHEMIST)

## Related Organs

| Organ | Relationship |
|-------|--------------|
| V (Public Process) | Upstream - receives API access for contributors |
| IV (Orchestration) | Coordinator - enforces gates |
| VII (Marketing) | Downstream - provides success stories |
| Alchemist (ivviiviivvi) | Potential merge candidate |
