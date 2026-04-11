"""Batch writer for InfluxDB time-series data."""

import logging
from datetime import datetime, timezone
from typing import Any

from influxdb_client import Point, WritePrecision
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync

from .register_map import Register, RegisterMap

logger = logging.getLogger(__name__)


class InfluxWriter:
    """Writes PM8000 readings to InfluxDB in batches."""

    def __init__(
        self,
        client: InfluxDBClientAsync,
        bucket: str,
        org: str,
        register_map: RegisterMap,
    ):
        self._client = client
        self._bucket = bucket
        self._org = org
        self._register_map = register_map

    async def write_readings(
        self,
        readings: dict[str, Any],
        measurement_id: str,
        device_id: str = "pm8000_01",
        timestamp: datetime | None = None,
    ):
        """Write a set of readings as InfluxDB points.

        Groups readings by category and phase to create efficient points.
        Each point has tags: measurement_id, device_id, phase
        and fields for each register value in that category+phase.
        """
        if not readings:
            return

        ts = timestamp or datetime.now(timezone.utc)
        points: list[Point] = []

        # Group readings by (category, phase)
        grouped: dict[tuple[str, str], dict[str, Any]] = {}
        for name, value in readings.items():
            reg = self._register_map.get_by_name(name)
            if reg is None:
                continue
            key = (reg.category, reg.phase)
            if key not in grouped:
                grouped[key] = {}
            # Use a shorter field name (strip category prefix if present)
            field_name = name
            grouped[key][field_name] = value

        for (category, phase), fields in grouped.items():
            point = (
                Point("power_metrics")
                .tag("measurement_id", measurement_id)
                .tag("device_id", device_id)
                .tag("phase", phase)
                .tag("category", category)
                .time(ts, WritePrecision.S)
            )
            for field_name, value in fields.items():
                if isinstance(value, float) and value == value:  # skip NaN
                    point.field(field_name, value)

            if point._fields:  # only add if has valid fields
                points.append(point)

        if points:
            try:
                write_api = self._client.write_api()
                await write_api.write(
                    bucket=self._bucket,
                    org=self._org,
                    record=points,
                )
            except Exception as e:
                logger.error(f"InfluxDB write error: {e}")
