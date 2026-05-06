from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str


@router.get("/healthz", response_model=HealthResponse, status_code=200)
async def healthz() -> HealthResponse:
    return HealthResponse(status="ok")
