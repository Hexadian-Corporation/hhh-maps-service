<critical>Note: This is a living document and will be updated as we refine our processes. Always refer back to this for the latest guidelines. Update whenever necessary.</critical>

# Copilot Instructions — hhh-maps-service

## Project Context

**H³ (Hexadian Hauling Helper)** is a Star Citizen companion app for managing hauling contracts, owned by **Hexadian Corporation** (GitHub org: `Hexadian-Corporation`).

This service manages **location and map data** — the hierarchy of systems, planets, moons, stations, cities, and outposts in the Star Citizen universe.

- **Repo:** `Hexadian-Corporation/hhh-maps-service`
- **Port:** 8003
- **Stack:** Python · FastAPI · MongoDB · pymongo · opyoid (DI) · pydantic-settings

## Architecture — Hexagonal (Ports & Adapters)

```
src/
├── main.py                          # FastAPI app factory + uvicorn
├── seed.py                          # Seed script for test locations
├── domain/
│   ├── models/                      # Pure dataclasses (no framework deps)
│   └── exceptions/                  # Domain-specific exceptions
├── application/
│   ├── ports/
│   │   ├── inbound/                 # Service interfaces (ABC)
│   │   └── outbound/               # Repository interfaces (ABC)
│   └── services/                    # Implementations of inbound ports
└── infrastructure/
    ├── config/
    │   ├── settings.py              # pydantic-settings (env prefix: HHH_MAPS_)
    │   └── dependencies.py          # opyoid DI Module
    └── adapters/
        ├── inbound/api/             # FastAPI router, DTOs (Pydantic), API mappers
        └── outbound/persistence/    # MongoDB repository, persistence mappers
```

**Key conventions:**
- Domain models are **pure Python dataclasses** — no Pydantic, no ORM
- DTOs at the API boundary are **Pydantic BaseModel** subclasses
- Mappers are **static classes** (`to_domain`, `to_dto`, `to_document`)
- DI uses **opyoid** (`Module`, `Injector`, `SingletonScope`)
- Repositories use **pymongo** directly (no ODM)
- Router pattern: **`init_router(service)` + module-level `router`** (standard pattern)

## Domain Model

- **Location** — `id`, `name`, `location_type`, `parent_id`, `coordinates` (Coordinates), `has_trade_terminal`, `has_landing_pad`, `landing_pad_size`
- **Coordinates** — `x`, `y`, `z` (all floats)

**`location_type` values:** `system` | `planet` | `moon` | `station` | `city` | `outpost`

**Hierarchy:** System → Planet/Moon → Station/City/Outpost. Top-level systems have `parent_id = None`.

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `HHH_MAPS_MONGO_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `HHH_MAPS_MONGO_DB` | `hhh_maps` | Database name |
| `HHH_MAPS_PORT` | `8003` | Service port |

## API

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/locations/` | Create a location |
| `GET` | `/locations/{id}` | Get location by ID |
| `GET` | `/locations/?location_type=` | Filter by type |
| `GET` | `/locations/?parent_id=` | Get children of a location |
| `GET` | `/locations/` | List all locations |
| `DELETE` | `/locations/{id}` | Delete a location |
| `GET` | `/health` | Health check |

## Issue & PR Title Format

**Format:** `<type>(maps): description`

- Example: `feat(maps): seed test locations`
- Example: `fix(maps): resolve seed data mutation bug`

**Allowed types:** `chore`, `fix`, `ci`, `docs`, `feat`, `refactor`, `test`, `build`, `perf`, `style`, `revert`

The issue title and PR title must be **identical**. PR body must include `Fixes #N`.

## Quality Standards

- `ruff check .` + `ruff format --check .` must pass
- `pytest --cov=src` with ≥90% coverage on changed lines (`diff-cover`)
- Type hints on all functions
- Squash merge only — PR title becomes the commit message

## Tooling

| Action | Command |
|--------|---------|
| Setup | `uv sync` |
| Run (dev) | `uv run uvicorn src.main:app --reload --port 8003` |
| Run in Docker | `uv run hhh up` (from monorepo root) |
| Test | `uv run pytest` |
| Lint | `uv run ruff check .` |
| Format | `uv run ruff format .` |

## Maintenance Rules

- **Keep the README up to date.** When you add, remove, or change commands, environment variables, API endpoints, domain models, or architecture — update `README.md`. The README is the source of truth for developers.
- **Keep the monorepo CLI service registry up to date.** When adding or removing a service, update `SERVICES`, `FRONTENDS`, `COMPOSE_SERVICE_MAP`, and `SERVICE_ALIASES` in `hhh-main/hhh_cli/__init__.py`, plus the `docker-compose.yml` entry.
