# hhh-maps-service

Location and map data management microservice for **H³ – Hexadian Hauling Helper**.

## Domain

Manages the Star Citizen universe map: star systems, planets, moons, stations, cities, and outposts. Tracks coordinates, trade terminals, and landing pad availability.

## Stack

- Python 3.11+ / FastAPI
- MongoDB (database: `hhh_maps`)
- opyoid (dependency injection)
- Hexagonal architecture (Ports & Adapters)

## Prerequisites

- [uv](https://docs.astral.sh/uv/)
- MongoDB running on localhost:27017

## Setup

```bash
uv sync
```

## Run

```bash
uv run uvicorn src.main:app --reload --port 8003
```

## Test

```bash
uv run pytest
```

## Lint

```bash
uv run ruff check .
```

## Format

```bash
uv run ruff format .
```

## Run in Docker (full stack)

From the monorepo root (`hexadian-hauling-helper`):

```bash
uv run hhh up
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `HHH_MAPS_MONGO_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `HHH_MAPS_MONGO_DB` | `hhh_maps` | Database name |
| `HHH_MAPS_PORT` | `8003` | Service port |
| `HHH_MAPS_JWT_SECRET` | `""` | Shared secret for JWT signature verification |
| `HHH_MAPS_JWT_ALGORITHM` | `HS256` | JWT signing algorithm |

## API

All endpoints except `/health` require a valid JWT bearer token. Write and delete operations require specific permissions.

| Method | Endpoint | Permission | Description |
|---|---|---|---|
| `GET` | `/health` | **Public** | Health check |
| `POST` | `/locations/` | `locations:write` | Create a location |
| `GET` | `/locations/{id}` | `locations:read` | Get location by ID |
| `GET` | `/locations/?location_type=` | `locations:read` | Filter by type |
| `GET` | `/locations/?parent_id=` | `locations:read` | Get children of a location |
| `GET` | `/locations/` | `locations:read` | List all locations |
| `GET` | `/locations/search?q=` | `locations:read` | Search locations by name |
| `PUT` | `/locations/{id}` | `locations:write` | Update a location (partial) |
| `DELETE` | `/locations/{id}` | `locations:delete` | Delete a location |
