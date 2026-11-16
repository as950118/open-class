# Architecture 0001: Modular Monolith

## Context

open-class is a multi-tenant academy SaaS centered on student-specific learning records. The product needs strict academy isolation and a small team should be able to evolve it without distributed-system overhead.

## Decision

- Keep a separately deployable React/TypeScript frontend and FastAPI REST backend.
- Run one modular FastAPI application; organize domain code by module under `backend/app` as domains arrive.
- Use PostgreSQL as the source of truth, SQLAlchemy 2 for persistence, and Alembic for all schema changes.
- Put API routes under `/api/v1`; keep request/response schemas separate from persistence models.
- Require tenant context and role permissions in backend service/dependency boundaries. Model academy ownership with foreign keys and composite constraints where needed.
- Keep recurring `Schedule` rules separate from dated `LessonSession` records; link session participants and per-student `LessonLog` entries explicitly.
- Store datetimes in UTC-aware form; display and interpret academy-local schedules in Asia/Seoul.
- Use PostgreSQL trigram indexes for initial lookup; keep search composition behind a search service.
- Compose frontend, backend, and PostgreSQL locally; defer Redis and service decomposition until a measured need exists.

## Phase 1 layout

`frontend/src` for the browser app; `backend/app/{api,core,models,schemas,services,permissions}` for the API and domains; `backend/alembic` for schema history. Compose owns local wiring. No product entities or fake dashboard aggregates are introduced in this phase.

## Consequences

The API can be deployed independently while transactional domain operations remain simple. Tenant enforcement must be consistently applied when each data module is built; DB ownership constraints provide a second boundary. A running service health endpoint checks the real database connection.
