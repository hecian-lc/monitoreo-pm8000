"""Pydantic models for devices."""

from pydantic import BaseModel, Field

# Supported meter models and their default register maps
METER_MODELS = {
    "PM8000": "pm8000_default.yaml",
    "PM5340": "pm5340_default.yaml",
    "PM2220": "pm2220_default.yaml",
}


class DeviceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    meter_model: str = Field(default="PM8000", pattern="^(PM8000|PM5340|PM2220)$")
    host: str = "192.168.1.100"
    port: int = 502
    unit_id: int = 1
    poll_interval: float = 1.0
    byte_order: str = "big"
    word_order: str = "big"


class DeviceUpdate(BaseModel):
    name: str | None = None
    meter_model: str | None = Field(default=None, pattern="^(PM8000|PM5340|PM2220)$")
    host: str | None = None
    port: int | None = None
    unit_id: int | None = None
    poll_interval: float | None = None
    byte_order: str | None = None
    word_order: str | None = None
    enabled: bool | None = None


class DeviceResponse(BaseModel):
    id: str
    name: str
    meter_model: str
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
