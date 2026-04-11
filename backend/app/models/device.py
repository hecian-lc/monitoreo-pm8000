"""Pydantic models for devices."""

from pydantic import BaseModel, Field


class DeviceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    host: str = "192.168.1.100"
    port: int = 502
    unit_id: int = 1
    poll_interval: float = 1.0
    register_map: str = "pm8000_default.yaml"
    byte_order: str = "big"
    word_order: str = "big"


class DeviceUpdate(BaseModel):
    name: str | None = None
    host: str | None = None
    port: int | None = None
    unit_id: int | None = None
    poll_interval: float | None = None
    register_map: str | None = None
    byte_order: str | None = None
    word_order: str | None = None
    enabled: bool | None = None


class DeviceResponse(BaseModel):
    id: str
    name: str
    host: str
    port: int
    unit_id: int
    poll_interval: float
    register_map: str
    byte_order: str
    word_order: str
    enabled: int
    created_at: str
    connected: bool = False
