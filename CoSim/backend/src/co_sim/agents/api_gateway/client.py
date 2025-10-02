from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx
from fastapi import HTTPException, Request, status

from co_sim.core.config import settings

SERVICE_MAP = {
    "auth": settings.service_endpoints.auth_base_url.rstrip("/"),
    "project": settings.service_endpoints.project_base_url.rstrip("/"),
    "session": settings.service_endpoints.session_base_url.rstrip("/"),
    "collab": settings.service_endpoints.collab_base_url.rstrip("/"),
}


async def forward_request(
    request: Request,
    service_key: str,
    path: str,
    method: str = "GET",
    json: Any | None = None,
    params: Mapping[str, Any] | None = None,
    content: Any | None = None,
) -> httpx.Response:
    base_url = SERVICE_MAP.get(service_key)
    if not base_url:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Service not configured")

    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() in {"authorization", "x-request-id", "content-type"}
    }

    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
        response = await client.request(
            method=method,
            url=f"{base_url}{path}",
            json=json,
            params=params,
            headers=headers,
            content=content,
        )

    if response.status_code >= 400:
        try:
            detail = response.json()
        except ValueError:
            detail = {"error": response.text}
        raise HTTPException(status_code=response.status_code, detail=detail)
    return response
