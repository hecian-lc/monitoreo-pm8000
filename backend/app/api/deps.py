"""Dependency injection for API endpoints."""

from ..collector.broadcast import BroadcastManager
from ..collector.service import CollectorService
from ..db.sqlite import Database

# These are set during app startup (lifespan)
db: Database | None = None
collector: CollectorService | None = None
broadcast: BroadcastManager | None = None
influx_client = None  # InfluxDBClientAsync


def get_db() -> Database:
    assert db is not None, "Database not initialized"
    return db


def get_collector() -> CollectorService:
    assert collector is not None, "Collector not initialized"
    return collector


def get_broadcast() -> BroadcastManager:
    assert broadcast is not None, "Broadcast not initialized"
    return broadcast


def get_influx():
    assert influx_client is not None, "InfluxDB not initialized"
    return influx_client
