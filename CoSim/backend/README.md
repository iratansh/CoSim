# CoSim Control Plane Services

Phase 1 implements the foundational control plane agents for the CoSim platform:

- Auth Agent (OIDC-ready authn/z, password flows, API keys)
- Project/Workspace Agent (projects, workspaces, datasets, templates, secrets)
- API Gateway Agent (tenanted REST entrypoint, rate-limits, routing to agents)

## Structure

```
backend/
  src/co_sim/
    agents/
    core/
    db/
    models/
    schemas/
    services/
``` 

## Quickstart

Create a virtual environment with Python 3.11 and install dependencies:

```bash
uv pip install -r <(uv pip compile pyproject.toml)
```

Run an agent (example for Auth):

```bash
uvicorn co_sim.agents.auth.main:app --reload --port 8001
```

Environment variables are documented in `src/co_sim/core/config.py`.

Database migrations use Alembic; configuration lives in `alembic/`.

## Containerized Dev Setup

A Docker workflow is available for local orchestration:

1. Copy `.env.example` to `.env` (optional for overrides).
2. Run `docker-compose up --build` from the repo root.
3. Services exposed:
   - Auth Agent on `localhost:8001`
   - Project Agent on `localhost:8002`
   - Session Orchestrator on `localhost:8003`
   - Collab Agent on `localhost:8004`
   - API Gateway on `localhost:8080`

The compose stack also provisions Postgres, Redis, and NATS for local testing.

### Seed the demo admin account

Run the helper script once to create the demo admin user used by the UI:

```bash
cd backend
PYTHONPATH=src python -m co_sim.scripts.seed_admin
```

This seeds `admin@cosim.dev` with password `adminadmin` (superuser privileges).

## Conda Environment

To work inside a Conda environment instead of Docker, from `backend/` run:

```bash
conda env create -f environment.yml
conda activate cosim
```

The environment installs the package in editable mode via `pip -e .`. Rerun `pip install -e .` after adding new dependencies.


## Frontend UI

The React web client lives in `../frontend`. Install dependencies with `npm install` and run `npm run dev` to launch the Vite dev server (proxying to the API gateway). The embedded IDE only exposes Python and C++ editors to keep the environment aligned with the platform scope.
