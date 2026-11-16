# ADR-0002: Modular Monolith

**Status:** Accepted (2026-11-16)

Use a separately served React frontend and one modular FastAPI backend with PostgreSQL. Keep product domains in modules and preserve API/schema boundaries. This avoids premature service operations while retaining a deployable frontend/backend split. See [project ADR](../../projects/open-class/adr/ADR-0002-modular-monolith.md).
