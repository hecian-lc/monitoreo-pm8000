"""Health check endpoint."""

from fastapi import APIRouter

from ..deps import get_collector

router = APIRouter()


@router.get("/health")
async def health_check():
    collector = get_collector()
    stats = collector.stats
    return {
        "status": "ok" if stats["connected"] else "degraded",
        **stats,
    }
