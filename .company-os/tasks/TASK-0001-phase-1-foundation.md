# Task: 프로젝트 기반 구성 및 로컬 실행 환경

| Field | Value |
|-------|-------|
| Task ID | TASK-0001 |
| Type | Feature |
| Status | Done |
| Assignee Role | Backend / Frontend / DevOps |
| Workflow | create-feature |
| Product | open-class |

## Links

- PRD: `projects/open-class/prd/PRD-0001-open-class.md`
- Architecture: `projects/open-class/architecture/ARCH-0001-modular-monolith.md`
- ADR: `projects/open-class/adr/ADR-0002-modular-monolith.md`

## Summary

Scaffold React + TypeScript + Vite and FastAPI + SQLAlchemy + Alembic, wire PostgreSQL with Docker Compose, and provide a Korean responsive shell with a real API/database health check.

## Acceptance Criteria

- [x] AC-1: Compose defines frontend, backend, PostgreSQL services and waits for DB readiness.
- [x] AC-2: FastAPI serves `/api/v1/health`, Swagger UI, and SQLAlchemy database connectivity.
- [x] AC-3: Alembic configuration and initial PostgreSQL migration are present.
- [x] AC-4: Korean responsive React layout calls the live health endpoint; no fake product metrics are shown.
- [x] AC-5: Root README, `.env.example`, PRD, architecture and ADR document how to start and evolve the project.
- [x] AC-6: `docker compose up --build` starts the stack and HTTP health checks succeed.

## Inputs (must read)

- `projects/open-class/prd/PRD-0001-open-class.md`
- `projects/open-class/architecture/ARCH-0001-modular-monolith.md`
- `docs/agent-collaboration-rules.md`

## Outputs (must produce)

- Compose-ready frontend/backend/database scaffold.
- Setup, architecture, PRD and task records.
- Local runtime verification result.

## Handoff

| From | To | Artifact |
|------|----|----------|
| PM | Architect | PRD-0001 |
| Architect | Implementer | ARCH-0001, ADR-0002 |
| Implementer | Reviewer/QA | Source tree and run results |

## Definition of Done

- [x] AC met
- [x] Compose stack is verified locally
- [ ] Review and QA recorded (deferred to project quality phase)
