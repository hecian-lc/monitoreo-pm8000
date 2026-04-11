"""Pydantic models for measurements."""

from pydantic import BaseModel, Field


class MeasurementCreate(BaseModel):
    device_id: str
    name: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    point_name: str = "T.G."


class MeasurementResponse(BaseModel):
    id: str
    device_id: str
    name: str
    description: str
    point_name: str
    status: str
    resolution: str
    created_at: str
    started_at: str | None = None
    stopped_at: str | None = None
    compressed_at: str | None = None


class MeasurementAction(BaseModel):
    action: str = Field(..., pattern="^(start|stop|compress)$")
