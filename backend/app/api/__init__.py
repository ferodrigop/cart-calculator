from __future__ import annotations

from fastapi import APIRouter

from app.api import auth, checkout, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(checkout.router)
