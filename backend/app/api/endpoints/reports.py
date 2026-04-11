"""Report generation endpoints."""

import asyncio
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ...config import settings
from ...models.report import ReportGenerateRequest, ScheduleCreate
from ...reports.generator import generate_report as run_report_generation
from ..deps import get_db, get_influx

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("")
async def list_reports(measurement_id: str | None = None):
    db = get_db()
    return await db.list_reports(measurement_id=measurement_id)


@router.post("/generate", status_code=202)
async def generate_report(body: ReportGenerateRequest):
    """Generate a DOCX/PDF report for a measurement.

    Returns immediately with report ID. Report is generated in background.
    """
    db = get_db()

    # Verify measurement exists
    m = await db.get_measurement(body.measurement_id)
    if not m:
        raise HTTPException(404, "Measurement not found")

    report_id = str(uuid.uuid4())[:8]
    report = await db.create_report(
        id=report_id,
        measurement_id=body.measurement_id,
        name=body.name,
        format=body.format,
        config={
            "cliente": body.cliente,
            "num_informe": body.num_informe,
            "atencion": body.atencion,
            "punto_medicion": body.punto_medicion or m["point_name"],
            "observaciones": body.observaciones,
            "observaciones_mode": body.observaciones_mode,
        },
    )

    # Trigger async report generation
    client = get_influx()
    asyncio.create_task(
        run_report_generation(
            report_id=report_id,
            measurement_id=body.measurement_id,
            influx_client=client,
            db=db,
            report_config_overrides={
                "cliente": body.cliente,
                "num_informe": body.num_informe,
                "atencion": body.atencion,
                "punto_medicion": body.punto_medicion or m["point_name"],
                "observaciones": body.observaciones,
                "observaciones_mode": body.observaciones_mode,
            },
        )
    )

    return report


@router.get("/{report_id}")
async def get_report(report_id: str):
    db = get_db()
    report = await db.get_report(report_id)
    if not report:
        raise HTTPException(404, "Report not found")
    return report


@router.get("/{report_id}/download")
async def download_report(report_id: str):
    db = get_db()
    report = await db.get_report(report_id)
    if not report:
        raise HTTPException(404, "Report not found")
    if report["status"] != "completed":
        raise HTTPException(400, f"Report status: {report['status']}")
    if not report["file_path"]:
        raise HTTPException(404, "Report file not found")

    file_path = Path(report["file_path"])
    if not file_path.exists():
        raise HTTPException(404, "Report file missing from disk")

    media_type = (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if report["format"] == "docx"
        else "application/pdf"
    )
    return FileResponse(
        file_path,
        media_type=media_type,
        filename=file_path.name,
    )


# ─── Schedules ───

@router.get("/schedules/list")
async def list_schedules():
    db = get_db()
    return await db.list_schedules()


@router.post("/schedules", status_code=201)
async def create_schedule(body: ScheduleCreate):
    db = get_db()
    schedule_id = str(uuid.uuid4())[:8]
    schedule = await db.create_schedule(
        id=schedule_id,
        name=body.name,
        cron_expression=body.cron_expression,
        config=body.config,
        measurement_id=body.measurement_id,
    )
    # TODO: Register with APScheduler (Phase 4)
    return schedule


@router.delete("/schedules/{schedule_id}")
async def delete_schedule(schedule_id: str):
    db = get_db()
    await db.delete_schedule(schedule_id)
    return {"status": "deleted"}


# ─── Report Config ───

@router.get("/config")
async def get_report_config():
    db = get_db()
    return await db.get_report_config()


@router.put("/config")
async def update_report_config(body: dict):
    db = get_db()
    if body:
        await db.update_report_config(**body)
    return await db.get_report_config()
