# Task: 학생별 수업 일지

| Field | Value |
|-------|-------|
| Task ID | TASK-0005 |
| Type | Feature |
| Status | In Progress |
| Assignee Role | Backend / Frontend |
| Workflow | create-feature |
| Product | open-class |

## Links

- PRD: `projects/open-class/prd/PRD-0001-open-class.md`
- Architecture: `projects/open-class/architecture/ARCH-0001-modular-monolith.md`

## Summary

Add student-specific lesson logs attached to real lesson sessions, with role-scoped CRUD, search filters and reusable timeline UI.

## Acceptance Criteria

- [ ] A teacher can create and update a log only for an assigned session participant.
- [ ] Admins can view academy logs; teachers and students see only their own records.
- [ ] Logs support course, teacher, student, date range and keyword filters.
- [ ] Student timeline and teacher/course log views use live API data.
- [ ] Tenant isolation and authorization tests pass.

## Definition of Done

- [ ] Migration, API, UI, tests and docs verified.
