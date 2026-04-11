"""Pydantic models for reports."""

from pydantic import BaseModel, Field


class ReportGenerateRequest(BaseModel):
    measurement_id: str
    name: str = "Informe"
    format: str = Field(default="docx", pattern="^(docx|pdf)$")
    # Report config overrides (optional - uses saved config if not provided)
    cliente: str | None = None
    num_informe: str | None = None
    atencion: str | None = None
    punto_medicion: str | None = None
    observaciones: str | None = None
    observaciones_mode: str = Field(default="auto", pattern="^(auto|gemini|manual)$")


class ReportResponse(BaseModel):
    id: str
    measurement_id: str
    name: str
    status: str
    format: str
    file_path: str | None = None
    created_at: str
    completed_at: str | None = None
    error_message: str | None = None


class ScheduleCreate(BaseModel):
    name: str
    measurement_id: str | None = None
    cron_expression: str
    config: dict = {}
    enabled: bool = True


class ScheduleResponse(BaseModel):
    id: str
    name: str
    measurement_id: str | None = None
    cron_expression: str
    config_json: str
    enabled: int
    last_run_at: str | None = None
    created_at: str
