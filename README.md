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
