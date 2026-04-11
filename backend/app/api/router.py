"""Top-level API router aggregation."""

from fastapi import APIRouter

from .endpoints import device, export, health, historical, measurements, realtime, reports

api_router = APIRouter(prefix="/api")

api_router.include_router(health.router)
api_router.include_router(measurements.router)
api_router.include_router(historical.router)
api_router.include_router(export.router)
api_router.include_router(reports.router)
api_router.include_router(device.router)

# WebSocket is mounted at root level, not under /api
ws_router = realtime.router
