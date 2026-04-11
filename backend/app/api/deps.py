"""Dependency injection for API endpoints."""

from ..collector.broadcast import BroadcastManager
from ..collector.service import CollectorManager
from ..db.sqlite import Database

# These are set during app startup (lifespan)
db: Database | None = None
collector_manager: CollectorManager | None = None
broadcast: BroadcastManager | None = None
influx_client = None  # InfluxDBClientAsync


def get_db() -> Database:
    assert db is not None, "Database not initialized"
    return db


def get_collector_manager() -> CollectorManager:
    assert collector_manager is not None, "CollectorManager not initialized"
    return collector_manager


def get_broadcast() -> BroadcastManager:
    assert broadcast is not None, "Broadcast not initialized"
    return broadcast


def get_influx():
    assert influx_client is not None, "InfluxDB not initialized"
    return influx_client
