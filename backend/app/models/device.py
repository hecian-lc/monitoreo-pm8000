"""Pydantic models for device configuration."""

from pydantic import BaseModel


class DeviceConfigUpdate(BaseModel):
    host: str | None = None
    port: int | None = None
    unit_id: int | None = None
    poll_interval: float | None = None
    register_map: str | None = None
    byte_order: str | None = None
    word_order: str | None = None


class DeviceConfigResponse(BaseModel):
    host: str
    port: int
    unit_id: int
    poll_interval: float
    register_map: str
    byte_order: str
    word_order: str
