"""FastAPI application with lifespan management."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .api import deps
from .api.router import api_router, ws_router
from .collector.broadcast import BroadcastManager
from .collector.service import CollectorManager
from .collector.writer import InfluxWriter
from .config import settings
from .db.influx import create_influx_client, setup_buckets, setup_downsampling_tasks
from .db.sqlite import Database
from .scheduler.service import SchedulerService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown of all services."""
    logger.info("Starting Monitoreo PM8000...")

    # 1. Connect to SQLite
    sqlite_path = settings.base_dir / settings.sqlite_path
    db = Database(str(sqlite_path))
    await db.connect()
    deps.db = db

    # 2. Connect to InfluxDB
    influx_client = await create_influx_client()
    deps.influx_client = influx_client

    try:
        await setup_buckets(influx_client)
        await setup_downsampling_tasks(influx_client)
    except Exception as e:
        logger.warning(f"InfluxDB setup warning: {e}")

    # 3. Create broadcast manager
    broadcast = BroadcastManager()
    deps.broadcast = broadcast

    # 4. Load register maps directory
    register_maps_dir = settings.base_dir / "registers"

    # 5. Create InfluxDB writer
    from .collector.register_map import load_register_map
    default_map = load_register_map(register_maps_dir / "pm8000_default.yaml")
    writer = InfluxWriter(
        client=influx_client,
        bucket=settings.influxdb_bucket,
        org=settings.influxdb_org,
        register_map=default_map,
    )

    # 6. Create CollectorManager for multi-device support
    collector_manager = CollectorManager(
        influx_writer=writer,
        broadcast=broadcast,
        register_maps_dir=register_maps_dir,
    )
    deps.collector_manager = collector_manager

    # 7. Load all devices from DB and start their collectors
    devices = await db.list_devices()
    for device in devices:
        try:
            await collector_manager.add_device(device)
        except Exception as e:
            logger.error(f"Failed to start collector for device {device['id']}: {e}")

    # 8. Resume any measurements that were recording
    measurements = await db.list_measurements()
    for m in measurements:
        if m["status"] == "recording":
            collector = collector_manager.get_collector(m["device_id"])
            if collector:
                collector.set_measurement(m["id"])
                logger.info(f"Resuming measurement: {m['name']} ({m['id']}) on device {m['device_id']}")

    # 9. Start scheduler for automatic reports
    scheduler = SchedulerService(db=db, influx_client=influx_client)
    await scheduler.start()

    # Ensure reports output directory exists
    reports_dir = settings.base_dir / settings.reports_output_dir
    reports_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Monitoreo PM8000 ready!")
    logger.info(f"  Devices loaded: {len(devices)}")
    logger.info(f"  InfluxDB: {settings.influxdb_url}")

    yield

    # Shutdown
    logger.info("Shutting down...")
    await scheduler.stop()
    await collector_manager.stop_all()
    await influx_client.close()
    await db.close()
    logger.info("Shutdown complete")


app = FastAPI(
    title="Monitoreo PM8000",
    description="Plataforma de monitoreo para Schneider Electric PM8000",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(api_router)
app.include_router(ws_router)

# Serve report files
reports_dir = Path(settings.reports_output_dir)
if reports_dir.exists():
    app.mount("/files", StaticFiles(directory=str(reports_dir)), name="files")


@app.get("/")
async def root():
    return {
        "name": "Monitoreo PM8000",
        "version": "0.1.0",
        "docs": "/docs",
    }
