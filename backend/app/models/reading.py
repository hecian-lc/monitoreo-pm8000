"""Pydantic models for data queries."""

from datetime import datetime

from pydantic import BaseModel, Field


class DataQueryParams(BaseModel):
    measurement_id: str
    start: datetime
    end: datetime
    variables: list[str] | None = None
    phases: list[str] | None = None
    categories: list[str] | None = None
    aggregate_fn: str = "mean"
    max_points: int = Field(default=5000, le=50000)


class DataRecord(BaseModel):
    time: str
    field: str
    value: float | None
    phase: str
    category: str


class HealthResponse(BaseModel):
    status: str
    collector_running: bool
    modbus_connected: bool
    active_measurement_id: str | None
    poll_interval: float
    cycle_time_ms: float
    total_cycles: int
    error_count: int
    ws_clients: int
