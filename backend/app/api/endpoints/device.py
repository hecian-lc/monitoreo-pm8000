"""Device CRUD endpoints - manage multiple PM8000 meters."""

import uuid

from fastapi import APIRouter, HTTPException

from ...models.device import DeviceCreate, DeviceUpdate
from ..deps import get_collector_manager, get_db

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("")
async def list_devices():
    db = get_db()
    cm = get_collector_manager()
    devices = await db.list_devices()
    # Enrich with connection status
    for d in devices:
        collector = cm.get_collector(d["id"])
        d["connected"] = collector.is_connected if collector else False
    return devices


@router.post("", status_code=201)
async def create_device(body: DeviceCreate):
    db = get_db()
    cm = get_collector_manager()
    device_id = str(uuid.uuid4())[:8]
    device = await db.create_device(
        id=device_id,
        name=body.name,
        host=body.host,
        port=body.port,
        unit_id=body.unit_id,
        poll_interval=body.poll_interval,
        register_map=body.register_map,
        byte_order=body.byte_order,
        word_order=body.word_order,
    )
    await cm.add_device(device)
    device["connected"] = False
    return device


@router.get("/{device_id}")
async def get_device(device_id: str):
    db = get_db()
    cm = get_collector_manager()
    device = await db.get_device(device_id)
    if not device:
        raise HTTPException(404, "Device not found")
    collector = cm.get_collector(device_id)
    device["connected"] = collector.is_connected if collector else False
    return device


@router.put("/{device_id}")
async def update_device(device_id: str, body: DeviceUpdate):
    db = get_db()
    cm = get_collector_manager()
    device = await db.get_device(device_id)
    if not device:
        raise HTTPException(404, "Device not found")
    updates = body.model_dump(exclude_none=True)
    if "enabled" in updates:
        updates["enabled"] = int(updates["enabled"])
    if updates:
        await db.update_device(device_id, **updates)
    device = await db.get_device(device_id)
    await cm.update_device(device)
    collector = cm.get_collector(device_id)
    device["connected"] = collector.is_connected if collector else False
    return device


@router.delete("/{device_id}")
async def delete_device(device_id: str):
    db = get_db()
    cm = get_collector_manager()
    device = await db.get_device(device_id)
    if not device:
        raise HTTPException(404, "Device not found")
    await cm.remove_device(device_id)
    await db.delete_device(device_id)
    return {"status": "deleted", "device_id": device_id}


@router.post("/{device_id}/test")
async def test_device_connection(device_id: str):
    db = get_db()
    cm = get_collector_manager()
    device = await db.get_device(device_id)
    if not device:
        raise HTTPException(404, "Device not found")
    ok = await cm.test_connection(device["host"], device["port"], device["unit_id"])
    return {"device_id": device_id, "connected": ok}


@router.get("/{device_id}/stats")
async def get_device_stats(device_id: str):
    cm = get_collector_manager()
    collector = cm.get_collector(device_id)
    if not collector:
        raise HTTPException(404, "Collector not found for device")
    return collector.stats
