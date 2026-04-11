"""Device configuration endpoints."""

from fastapi import APIRouter

from ...models.device import DeviceConfigUpdate
from ..deps import get_db

router = APIRouter(prefix="/device", tags=["device"])


@router.get("/config")
async def get_device_config():
    db = get_db()
    return await db.get_device_config()


@router.put("/config")
async def update_device_config(body: DeviceConfigUpdate):
    db = get_db()
    updates = body.model_dump(exclude_none=True)
    if updates:
        await db.update_device_config(**updates)
    return await db.get_device_config()


@router.get("/report-config")
async def get_report_config():
    db = get_db()
    return await db.get_report_config()


@router.put("/report-config")
async def update_report_config(body: dict):
    db = get_db()
    if body:
        await db.update_report_config(**body)
    return await db.get_report_config()
