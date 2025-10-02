#!/usr/bin/env bash
set -euo pipefail

APP_MODULE=${COSIM_APP_MODULE:-co_sim.agents.api_gateway.main:app}
HOST=${COSIM_HOST:-0.0.0.0}
PORT=${COSIM_PORT:-8000}
RELOAD=${COSIM_RELOAD:-false}

if [[ "${1:-}" == "alembic" ]]; then
  shift
  exec alembic "$@"
fi

if [[ "${RELOAD}" == "true" ]]; then
  exec uvicorn "$APP_MODULE" --host "$HOST" --port "$PORT" --reload
else
  exec uvicorn "$APP_MODULE" --host "$HOST" --port "$PORT"
fi
