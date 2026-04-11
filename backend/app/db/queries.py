"""Flux query builders for InfluxDB data retrieval."""

import logging
from datetime import datetime, timedelta
from typing import Any

from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync

from ..config import settings

logger = logging.getLogger(__name__)


def _select_bucket(start: datetime, end: datetime) -> str:
    """Auto-select the best bucket based on time range duration."""
    duration = end - start
    if duration <= timedelta(hours=1):
        return settings.influxdb_bucket          # raw (1s)
    elif duration <= timedelta(hours=24):
        return settings.influxdb_bucket_1min      # 1 min
    elif duration <= timedelta(days=30):
        return settings.influxdb_bucket_15min     # 15 min
    else:
        return settings.influxdb_bucket_1hour     # 1 hour


def _select_window(start: datetime, end: datetime, max_points: int = 5000) -> str:
    """Calculate aggregation window to limit data points for charts."""
    duration = end - start
    total_seconds = duration.total_seconds()

    # Calculate minimum window to stay under max_points
    min_window_s = total_seconds / max_points
    if min_window_s <= 1:
        return ""  # No aggregation needed
    elif min_window_s <= 60:
        return "1m"
    elif min_window_s <= 300:
        return "5m"
    elif min_window_s <= 900:
        return "15m"
    elif min_window_s <= 3600:
        return "1h"
    else:
        hours = max(1, int(min_window_s / 3600))
        return f"{hours}h"


def build_query(
    measurement_id: str,
    start: datetime,
    end: datetime,
    variables: list[str] | None = None,
    phases: list[str] | None = None,
    categories: list[str] | None = None,
    bucket: str | None = None,
    aggregate_window: str | None = None,
    aggregate_fn: str = "mean",
    max_points: int = 5000,
) -> str:
    """Build a Flux query for historical data.

    Args:
        measurement_id: Filter by measurement
        start: Start time (inclusive)
        end: End time (inclusive)
        variables: Filter by specific field names (e.g., ["voltage_an", "current_a"])
        phases: Filter by phase tags (e.g., ["a", "b", "c"])
        categories: Filter by category tags (e.g., ["voltage", "current"])
        bucket: Override auto-selected bucket
        aggregate_window: Override auto-calculated aggregation window
        aggregate_fn: Aggregation function (mean, min, max, last)
        max_points: Maximum data points to return

    Returns:
        Flux query string
    """
    selected_bucket = bucket or _select_bucket(start, end)
    window = aggregate_window or _select_window(start, end, max_points)

    start_str = start.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_str = end.strftime("%Y-%m-%dT%H:%M:%SZ")

    parts = [
        f'from(bucket: "{selected_bucket}")',
        f'  |> range(start: {start_str}, stop: {end_str})',
        f'  |> filter(fn: (r) => r._measurement == "power_metrics")',
        f'  |> filter(fn: (r) => r.measurement_id == "{measurement_id}")',
    ]

    if phases:
        phase_filter = " or ".join(f'r.phase == "{p}"' for p in phases)
        parts.append(f"  |> filter(fn: (r) => {phase_filter})")

    if categories:
        cat_filter = " or ".join(f'r.category == "{c}"' for c in categories)
        parts.append(f"  |> filter(fn: (r) => {cat_filter})")

    if variables:
        var_filter = " or ".join(f'r._field == "{v}"' for v in variables)
        parts.append(f"  |> filter(fn: (r) => {var_filter})")

    if window:
        parts.append(
            f"  |> aggregateWindow(every: {window}, fn: {aggregate_fn}, createEmpty: false)"
        )

    return "\n".join(parts)


async def query_data(
    client: InfluxDBClientAsync,
    measurement_id: str,
    start: datetime,
    end: datetime,
    variables: list[str] | None = None,
    phases: list[str] | None = None,
    categories: list[str] | None = None,
    aggregate_fn: str = "mean",
    max_points: int = 5000,
) -> list[dict[str, Any]]:
    """Query historical data and return as list of dicts.

    Returns:
        List of dicts with keys: time, field, value, phase, category
    """
    flux = build_query(
        measurement_id=measurement_id,
        start=start,
        end=end,
        variables=variables,
        phases=phases,
        categories=categories,
        aggregate_fn=aggregate_fn,
        max_points=max_points,
    )

    query_api = client.query_api()
    tables = await query_api.query(flux, org=settings.influxdb_org)

    results: list[dict[str, Any]] = []
    for table in tables:
        for record in table.records:
            results.append({
                "time": record.get_time().isoformat(),
                "field": record.get_field(),
                "value": record.get_value(),
                "phase": record.values.get("phase", ""),
                "category": record.values.get("category", ""),
                "measurement_id": record.values.get("measurement_id", ""),
            })

    return results


async def query_stats(
    client: InfluxDBClientAsync,
    measurement_id: str,
    start: datetime,
    end: datetime,
    variables: list[str] | None = None,
) -> dict[str, dict[str, float]]:
    """Query min/max/mean/last for each variable.

    Returns:
        Dict mapping field name to {min, max, mean, last} values
    """
    bucket = _select_bucket(start, end)
    start_str = start.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_str = end.strftime("%Y-%m-%dT%H:%M:%SZ")

    stats: dict[str, dict[str, float]] = {}

    for fn_name in ["min", "max", "mean", "last"]:
        flux = f'''
from(bucket: "{bucket}")
  |> range(start: {start_str}, stop: {end_str})
  |> filter(fn: (r) => r._measurement == "power_metrics")
  |> filter(fn: (r) => r.measurement_id == "{measurement_id}")
  |> {fn_name}()
'''
        if variables:
            var_filter = " or ".join(f'r._field == "{v}"' for v in variables)
            flux = flux.replace(
                f"|> {fn_name}()",
                f"|> filter(fn: (r) => {var_filter})\n  |> {fn_name}()",
            )

        query_api = client.query_api()
        tables = await query_api.query(flux, org=settings.influxdb_org)

        for table in tables:
            for record in table.records:
                field = record.get_field()
                if field not in stats:
                    stats[field] = {}
                stats[field][fn_name] = record.get_value()

    return stats


async def delete_measurement_data(
    client: InfluxDBClientAsync,
    measurement_id: str,
    bucket: str | None = None,
):
    """Delete all data for a measurement from a bucket."""
    target_bucket = bucket or settings.influxdb_bucket
    delete_api = client.delete_api()

    await delete_api.delete(
        start=datetime(2020, 1, 1),
        stop=datetime(2099, 12, 31),
        predicate=f'measurement_id="{measurement_id}"',
        bucket=target_bucket,
        org=settings.influxdb_org,
    )
    logger.info(f"Deleted data for measurement '{measurement_id}' from '{target_bucket}'")
