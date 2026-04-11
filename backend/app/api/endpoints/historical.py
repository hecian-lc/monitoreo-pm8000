"""Historical data query endpoint."""

from datetime import datetime

from fastapi import APIRouter, Query

from ...db.queries import query_data, query_stats
from ..deps import get_influx

router = APIRouter(prefix="/data", tags=["data"])


@router.get("/query")
async def get_historical_data(
    measurement_id: str,
    start: datetime,
    end: datetime,
    variables: list[str] | None = Query(None),
    phases: list[str] | None = Query(None),
    categories: list[str] | None = Query(None),
    aggregate_fn: str = "mean",
    max_points: int = Query(5000, le=50000),
):
    """Query historical data for a measurement.

    Auto-selects resolution based on time range:
    - < 1h: raw (1s)
    - < 24h: 1 minute
    - < 30d: 15 minutes
    - > 30d: 1 hour
    """
    client = get_influx()
    data = await query_data(
        client,
        measurement_id=measurement_id,
        start=start,
        end=end,
        variables=variables,
        phases=phases,
        categories=categories,
        aggregate_fn=aggregate_fn,
        max_points=max_points,
    )
    return {"count": len(data), "data": data}


@router.get("/stats")
async def get_data_stats(
    measurement_id: str,
    start: datetime,
    end: datetime,
    variables: list[str] | None = Query(None),
):
    """Get min/max/mean/last statistics for each variable."""
    client = get_influx()
    stats = await query_stats(
        client,
        measurement_id=measurement_id,
        start=start,
        end=end,
        variables=variables,
    )
    return stats
