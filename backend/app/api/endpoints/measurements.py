"""CRUD endpoints for measurements (named recording sessions)."""

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException

from ...db import queries as influx_queries
from ..deps import get_collector, get_db, get_influx
from ...models.measurement import (
    MeasurementAction,
    MeasurementCreate,
    MeasurementResponse,
)

router = APIRouter(prefix="/measurements", tags=["measurements"])


@router.get("", response_model=list[MeasurementResponse])
async def list_measurements():
    db = get_db()
    return await db.list_measurements()


@router.post("", response_model=MeasurementResponse, status_code=201)
async def create_measurement(body: MeasurementCreate):
    db = get_db()
    measurement_id = str(uuid.uuid4())[:8]
    measurement = await db.create_measurement(
        id=measurement_id,
        name=body.name,
        description=body.description,
        point_name=body.point_name,
    )
    return measurement


@router.get("/{measurement_id}", response_model=MeasurementResponse)
async def get_measurement(measurement_id: str):
    db = get_db()
    m = await db.get_measurement(measurement_id)
    if not m:
        raise HTTPException(404, "Measurement not found")
    return m


@router.post("/{measurement_id}/action")
async def measurement_action(measurement_id: str, body: MeasurementAction):
    """Start, stop, or compress a measurement."""
    db = get_db()
    collector = get_collector()

    m = await db.get_measurement(measurement_id)
    if not m:
        raise HTTPException(404, "Measurement not found")

    now = datetime.utcnow().isoformat()

    if body.action == "start":
        if m["status"] == "recording":
            raise HTTPException(400, "Measurement already recording")
        # Stop any other active measurement
        if collector.active_measurement_id:
            await db.update_measurement_status(
                collector.active_measurement_id, "stopped", stopped_at=now
            )
        collector.set_measurement(measurement_id)
        await db.update_measurement_status(
            measurement_id, "recording", started_at=now
        )
        return {"status": "recording", "measurement_id": measurement_id}

    elif body.action == "stop":
        if collector.active_measurement_id == measurement_id:
            collector.set_measurement(None)
        await db.update_measurement_status(
            measurement_id, "stopped", stopped_at=now
        )
        return {"status": "stopped", "measurement_id": measurement_id}

    elif body.action == "compress":
        if m["status"] == "recording":
            raise HTTPException(400, "Cannot compress while recording")
        if m["status"] == "compressed":
            raise HTTPException(400, "Already compressed")

        # Delete raw data (downsampled buckets retain the aggregated data)
        client = get_influx()
        await influx_queries.delete_measurement_data(
            client, measurement_id, bucket=None  # deletes from pm_raw
        )
        await db.update_measurement_status(
            measurement_id, "compressed",
            resolution="1min", compressed_at=now,
        )
        return {"status": "compressed", "measurement_id": measurement_id}


@router.delete("/{measurement_id}")
async def delete_measurement(measurement_id: str):
    """Delete a measurement and all its data."""
    db = get_db()
    collector = get_collector()
    client = get_influx()

    m = await db.get_measurement(measurement_id)
    if not m:
        raise HTTPException(404, "Measurement not found")

    # Stop if currently recording
    if collector.active_measurement_id == measurement_id:
        collector.set_measurement(None)

    # Delete from all InfluxDB buckets
    from ...config import settings
    for bucket in [
        settings.influxdb_bucket,
        settings.influxdb_bucket_1min,
        settings.influxdb_bucket_15min,
        settings.influxdb_bucket_1hour,
    ]:
        try:
            await influx_queries.delete_measurement_data(
                client, measurement_id, bucket=bucket
            )
        except Exception:
            pass  # Bucket might not exist yet

    # Delete from SQLite
    await db.delete_measurement(measurement_id)
    return {"status": "deleted", "measurement_id": measurement_id}
