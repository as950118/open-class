# Task: 최종 품질 및 실행 검증

| Field | Value |
|-------|-------|
| Task ID | TASK-0007 |
| Type | Chore |
| Status | Done |
| Assignee Role | Backend / DevOps / QA |
| Workflow | release |
| Product | open-class |

## Links

- PRD: `projects/open-class/prd/PRD-0001-open-class.md`
- Architecture: `projects/open-class/architecture/ARCH-0001-modular-monolith.md`

## Summary

Run the end-to-end local stack, verify migrations and role/tenant boundaries, and document configuration and test commands.

## Acceptance Criteria

- [x] Compose starts frontend, backend and PostgreSQL; Alembic is at `0006_search_trigram_indexes`.
- [x] Production cookie/JWT settings reject development secrets and invalid expiry values.
- [x] Backend permission/tenant tests (10 passed) and frontend production build pass.
- [x] README explains setup, seed, tests and implemented features.

## Definition of Done

- [x] Compose health is OK, PostgreSQL is connected, frontend responds HTTP 200, migrations and tests are verified.
