# Task: 통합 검색과 운영 대시보드

| Field | Value |
|-------|-------|
| Task ID | TASK-0006 |
| Type | Feature |
| Status | Done |
| Assignee Role | Backend / Frontend |
| Workflow | create-feature |
| Product | open-class |

## Links

- PRD: `projects/open-class/prd/PRD-0001-open-class.md`
- Architecture: `projects/open-class/architecture/ARCH-0001-modular-monolith.md`

## Summary

Provide role-scoped dashboard statistics, today's lessons and missing journals, plus one API-backed search across academy records.

## Acceptance Criteria

- [x] Dashboard counts and activity load from the API using Asia/Seoul day boundaries.
- [x] Missing lesson journals count completed session participants without a journal.
- [x] Search combines student, teacher, course and lesson-log filters while respecting tenant and role access.
- [x] Header search and dashboard actions navigate to real records.
- [x] Backend authorization tests and frontend production build pass (9 backend tests).

## Definition of Done

- [x] Migration (0006 trigram indexes), API, UI, tests and docs verified; local PostgreSQL migration head is 0006.
