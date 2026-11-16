# Task: 학원 기본 데이터 관리

| Field | Value |
|-------|-------|
| Task ID | TASK-0003 |
| Type | Feature |
| Status | Done |
| Assignee Role | Backend / Frontend |
| Workflow | create-feature |
| Product | open-class |

## Links

- PRD: `projects/open-class/prd/PRD-0001-open-class.md`
- Architecture: `projects/open-class/architecture/ARCH-0001-modular-monolith.md`

## Summary

Implement tenant-scoped teacher, student, subject, course, and enrollment records with validated relationships and usable list/create/update UI flows.

## Acceptance Criteria

- [x] AC-1: Each profile/course/enrollment has database constraints and tenant-safe foreign-key relationships.
- [x] AC-2: Admin create/update endpoints are academy-scoped and teacher/student reads are limited to their records.
- [x] AC-3: Teacher, student, course, subject, and enrollment views load and write through REST APIs.
- [x] AC-4: Enrollment prevents cross-academy links and duplicate registrations.
- [x] AC-5: Migrations, validation, and permission tests pass (8 backend tests).

## Inputs (must read)

- `projects/open-class/prd/PRD-0001-open-class.md`
- `projects/open-class/architecture/ARCH-0001-modular-monolith.md`
- `docs/agent-collaboration-rules.md`

## Outputs (must produce)

- Tenant-scoped models, schemas, API and frontend pages.
- Alembic migration and test coverage.

## Handoff

| From | To | Artifact |
|------|----|----------|
| Architect | Implementer | ARCH-0001, PRD-0001 |
| Implementer | Reviewer/QA | APIs, UI, migration, tests |

## Definition of Done

- [x] AC met
- [x] Compose, migrations and frontend production build verified
- [ ] Review and QA recorded (deferred to project quality phase)
