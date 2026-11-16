# Task: 반복 시간표와 실제 수업 회차

| Field | Value |
|-------|-------|
| Task ID | TASK-0004 |
| Type | Feature |
| Status | Done |
| Assignee Role | Backend / Frontend |
| Workflow | create-feature |
| Product | open-class |

## Links

- PRD: `projects/open-class/prd/PRD-0001-open-class.md`
- Architecture: `projects/open-class/architecture/ARCH-0001-modular-monolith.md`

## Summary

Create weekly recurring schedules, reject teacher time conflicts, expand a date range into real sessions in Asia/Seoul, snapshot enrolled students, and expose schedule/session management APIs and UI.

## Acceptance Criteria

- [x] AC-1: Repeating rules and dated sessions are separate tenant-scoped entities.
- [x] AC-2: Overlapping schedule rules for the same teacher are rejected over intersecting effective dates.
- [x] AC-3: Session generation is bounded, timezone-aware and idempotent; active enrollments become session participants.
- [x] AC-4: Admin, assigned teacher and enrolled student session views are tenant/role scoped.
- [x] AC-5: Week schedule screen uses real API data and changes persist to PostgreSQL.
- [x] AC-6: Schedule, overlap, generation, attendance access and tenant-boundary tests pass (9 backend tests).

## Inputs (must read)

- `projects/open-class/prd/PRD-0001-open-class.md`
- `projects/open-class/architecture/ARCH-0001-modular-monolith.md`
- `docs/agent-collaboration-rules.md`

## Outputs (must produce)

- Schedule and lesson-session models, API, frontend and migration.
- Permission and business-rule tests.

## Handoff

| From | To | Artifact |
|------|----|----------|
| Architect | Implementer | ARCH-0001, PRD-0001 |
| Implementer | Reviewer/QA | API, UI, migration, tests |

## Definition of Done

- [x] AC met
- [x] Compose, migrations and frontend build verified
- [x] Review and QA recorded: local health/API DB connection, frontend HTTP 200, 9 backend tests pass.
