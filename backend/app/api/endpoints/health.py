"""Health check endpoint."""

from fastapi import APIRouter

from ..deps import get_broadcast, get_collector_manager

router = APIRouter()


@router.get("/health")
async def health_check():
    cm = get_collector_manager()
    broadcast = get_broadcast()
    all_stats = cm.get_all_stats()
    any_connected = any(s["connected"] for s in all_stats)
    return {
        "status": "ok" if any_connected else "degraded",
        "devices": all_stats,
        "ws_clients": broadcast.client_count,
    }
