# API Gateway Service

## Purpose
FastAPI REST application exposing versioned prediction, routing hazard alerts, and localized natural language hotspot explanations.

## Endpoints
- `GET /health`: Liveness and readiness health checks.
- `GET /metrics`: Service telemetry and active cache backend information.
- `POST /v1/predict`: Batch edge-level probability forecasts for the next 1-hour window.
- `POST /v1/route-check`: Vehicle route safety evaluation with Valhalla hazard detours.
- `GET /v1/hotspots`: List active clusters where predicted risk $> 80\%$.
- `GET /v1/hotspots/{cluster_id}/explanation`: Retrieve causative natural-language statements and driver advisories.

## Authentication & Production Hardening (Patch 9)
> [!NOTE]
> **Authentication Scope**: Version 1 ships without authentication or rate-limiting for standalone demonstration and development. Production deployment requires configuring an API-key header (`X-API-Key`) or OAuth2 / OpenID Connect middleware proxy before exposing to public networks.

## Running Locally
```bash
uvicorn services.api_gateway.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive Swagger documentation is available at `http://localhost:8000/docs`.
