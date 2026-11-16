# Task: 인증, 역할 권한 및 학원별 사용자 격리

| Field | Value |
|-------|-------|
| Task ID | TASK-0002 |
| Type | Feature |
| Status | Done |
| Assignee Role | Backend / Frontend |
| Workflow | create-feature |
| Product | open-class |

## Links

- PRD: `projects/open-class/prd/PRD-0001-open-class.md`
- Architecture: `projects/open-class/architecture/ARCH-0001-modular-monolith.md`
- ADR: `projects/open-class/adr/ADR-0002-modular-monolith.md`

## Summary

Add academy and user persistence, secure password hashing, JWT-backed HTTP-only sessions, role checks, tenant-scoped user management, and a real login/profile/logout flow.

## Acceptance Criteria

- [x] AC-1: Login uses Argon2 password hashes and an HTTP-only, same-site session cookie.
- [x] AC-2: API validates active users, token expiry and role permissions on the server.
- [x] AC-3: Academy administrators only read and create users in their academy; platform administrators may manage academies.
- [x] AC-4: The UI logs in, loads the current account from the API, and logs out.
- [x] AC-5: Alembic migrations and a manual development seed command create test accounts safely.
- [x] AC-6: Permission and tenant-boundary behavior is verified by six passing backend tests.

## Inputs (must read)

- `projects/open-class/prd/PRD-0001-open-class.md`
- `projects/open-class/architecture/ARCH-0001-modular-monolith.md`
- `docs/agent-collaboration-rules.md`

## Outputs (must produce)

- Authentication and user API.
- Identity schema migration and seed command.
- Authenticated Korean frontend shell.
- Verification record.

## Handoff

| From | To | Artifact |
|------|----|----------|
| PM | Architect | PRD-0001 |
| Architect | Implementer | ARCH-0001, ADR-0002 |
| Implementer | Reviewer/QA | API, migration, auth UI, verification |

## Definition of Done

- [x] AC met
- [x] Authenticated app runs in Compose
- [ ] Review and QA recorded (deferred to project quality phase)
