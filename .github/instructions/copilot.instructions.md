<critical>**Configuration externalization:** Any new configuration value that could vary between environments (URLs, secrets, ports, origins, timeouts, cache sizes, etc.) MUST be externalized as a `Settings` field with an environment variable and a sensible default. After adding it, also create a task in `hexadian-hauling-helper` to wire the variable in `docker-compose.yml`.</critical>

<critical>Note: This is a living document and will be updated as we refine our processes. Always refer back to this for the latest guidelines. Update whenever necessary.</critical>

<critical>**Development Workflow:** All changes go through a branch + PR — no direct commits to `main` unless explicitly instructed. See `.github/instructions/development-workflow.instructions.md`.</critical>

<critical>**PR and Issue linkage:** When creating a pull request from an issue, always mention the issue number in the PR description using `Fixes #N`, `Closes #N`, or `Resolves #N`. This is required for GitHub to auto-close the issue on merge.</critical>

<critical>**Before starting implementation:** Read ALL instruction files in `.github/instructions/` of this repository. Also read the organization-level instructions from the `Hexadian-Corporation/.github` repository (`.github/instructions/` directory). These contain essential rules for workflow, bug history, domain models, and GitHub procedures that you MUST follow.</critical>

<critical>**PR title:** The PR title MUST be identical to the originating issue title. Set the final PR title (remove the `[WIP]` prefix) before beginning implementation, not after.</critical>

<critical>**Async & Parallelization:** All new Python code MUST be async-first. See `async-and-parallelization.instructions.md` for mandatory rules on motor, asyncio.gather, and parallelization patterns.</critical>

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
| `HHH_MAPS_HOST` | `0.0.0.0` | Host address to bind the server |
| `HHH_MAPS_PORT` | `8003` | Service port |
| `HEXADIAN_AUTH_JWT_SECRET` | `change-me-in-production` | Shared secret for JWT signature verification |
| `HHH_MAPS_JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `HHH_MAPS_CORS_ORIGINS` | `["http://localhost:3000","http://localhost:3001"]` | Allowed CORS origins (JSON array) |
| `HHH_MAPS_CACHE_TTL_SECONDS` | `300` | TTL in seconds for in-memory location and distance caches |
| `HHH_MAPS_LOCATION_CACHE_MAXSIZE` | `256` | Maximum entries for the location cache |
| `HHH_MAPS_DISTANCE_CACHE_MAXSIZE` | `512` | Maximum entries for the distance cache |

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

## CI & Branch Protection

**Required status checks** (all with `app_id: 15368` — GitHub Actions):
- `Lint & Format` — `ruff check .` + `ruff format --check .`
- `Tests & Coverage` — `pytest` + `diff-cover` (≥90% on changed lines)
- `Validate PR Title` — conventional commit format
- `Secret Scan` — gitleaks

> **Critical:** Required status checks must always use `app_id: 15368` (GitHub Actions). Using `app_id: null` causes checks to freeze as "Expected — Waiting for status" for any check name not previously reported on `main`. See BUG-011.

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
- **Keep the monorepo CLI service registry up to date.** When adding or removing a service, update `SERVICES`, `FRONTENDS`, `COMPOSE_SERVICE_MAP`, and `SERVICE_ALIASES` in `hexadian-hauling-helper/hhh_cli/__init__.py`, plus the `docker-compose.yml` entry.

## Organization Profile Maintenance

- **Keep the org profile README up to date.** When repositories, ports, architecture, workflows, security policy, or ownership change, update Hexadian-Corporation/.github/profile/README.md in the public .github repo.
- **Treat the org profile as canonical org summary.** Ensure descriptions in this repo remain consistent with the organization profile README.

Remember, before finishing: resolve any merge conflict and merge source (PR origin and destination) branch into current one.