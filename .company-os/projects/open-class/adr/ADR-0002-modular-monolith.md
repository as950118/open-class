# ADR-0002: Use a Modular Monolith

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-11-16 |
| Decision owners | Product / Architecture |

## Context

The product has related transactional domains and tenant isolation requirements. Early microservices would add operational cost without a demonstrated scaling need.

## Decision

Use an independently served React client and a single modular FastAPI backend with PostgreSQL. Organize backend domain code into modules and keep service/repository boundaries explicit when the domains are implemented.

## Consequences

The initial local environment is small and transactions stay straightforward. Module boundaries and tenant-scoped data access need deliberate enforcement as features are added.
