"""FastAPI descriptive statistics service with an exact-origin CORS policy."""

from __future__ import annotations

import os
import time
import uuid
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp, Message, Receive, Scope, Send

ALLOWED_ORIGIN = "https://dash-scfih4.example.com"
APP_EMAIL = os.getenv("APP_EMAIL", "").strip()


class RequestMetricsMiddleware:
    """Add per-request headers to every HTTP response, including CORS preflights."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = str(uuid.uuid4())
        started = time.perf_counter()

        async def send_with_metrics(message: Message) -> None:
            if message["type"] == "http.response.start":
                elapsed = max(0.0, time.perf_counter() - started)
                headers = [
                    (name, value)
                    for name, value in message.get("headers", [])
                    if name.lower() not in (b"x-request-id", b"x-process-time")
                ]
                headers.append((b"x-request-id", request_id.encode("ascii")))
                headers.append((b"x-process-time", f"{elapsed:.6f}".encode("ascii")))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_metrics)


api = FastAPI(title="Descriptive Statistics API", version="1.0.0")

# Exact origin allowlist: deliberately no wildcard origin.
api.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
    max_age=600,
)


@api.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@api.get("/stats")
def stats(values: str = Query(..., description="Comma-separated integers")) -> dict[str, Any]:
    """Return exact descriptive statistics for the submitted integer batch."""
    if not APP_EMAIL:
        raise HTTPException(
            status_code=500,
            detail="The service owner must set APP_EMAIL to their logged-in email address.",
        )

    parts = values.split(",")
    if not parts or any(not part.strip() for part in parts):
        raise HTTPException(status_code=422, detail="values must be a comma-separated list of integers")

    try:
        numbers = [int(part.strip()) for part in parts]
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail="values must contain only comma-separated integers",
        ) from exc

    total = sum(numbers)
    count = len(numbers)
    return {
        "email": APP_EMAIL,
        "count": count,
        "sum": total,
        "min": min(numbers),
        "max": max(numbers),
        "mean": total / count,
    }


# Wrap the FastAPI app externally so headers also cover CORS middleware responses.
app = RequestMetricsMiddleware(api)
