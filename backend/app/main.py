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
from .collector.modbus_client import PM8000Client
from .collector.register_map import load_register_map
from .collector.service import CollectorService
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

    # 1. Load register map
    register_map_path = settings.base_dir / settings.register_map_path
    register_map = load_register_map(register_map_path)
    logger.info(
        f"Loaded {len(register_map.registers)} registers "
        f"in {len(register_map.blocks)} blocks"
    )

    # 2. Connect to SQLite
    sqlite_path = settings.base_dir / settings.sqlite_path
    db = Database(str(sqlite_path))
    await db.connect()
    deps.db = db

    # Load device config from DB (may override env defaults)
    device_config = await db.get_device_config()

    # 3. Connect to InfluxDB
    influx_client = await create_influx_client()
    deps.influx_client = influx_client

    # Setup buckets and downsampling
    try:
        await setup_buckets(influx_client)
        await setup_downsampling_tasks(influx_client)
    except Exception as e:
        logger.warning(f"InfluxDB setup warning: {e}")

    # 4. Create broadcast manager
    broadcast = BroadcastManager()
    deps.broadcast = broadcast

    # 5. Create Modbus client
    modbus_host = device_config.get("host", settings.modbus_host)
    modbus_port = device_config.get("port", settings.modbus_port)
    modbus_unit = device_config.get("unit_id", settings.modbus_unit_id)
    poll_interval = device_config.get("poll_interval", settings.poll_interval)

    modbus_client = PM8000Client(
        host=modbus_host,
        port=modbus_port,
        unit_id=modbus_unit,
    )

    # 6. Create InfluxDB writer
    writer = InfluxWriter(
        client=influx_client,
        bucket=settings.influxdb_bucket,
        org=settings.influxdb_org,
        register_map=register_map,
    )

    # 7. Create and start collector service
    collector = CollectorService(
        modbus_client=modbus_client,
        influx_writer=writer,
        register_map=register_map,
        broadcast=broadcast,
        poll_interval=poll_interval,
    )
    deps.collector = collector

    # Check for any measurement that was recording when we last shut down
    measurements = await db.list_measurements()
    for m in measurements:
        if m["status"] == "recording":
            collector.set_measurement(m["id"])
            logger.info(f"Resuming measurement: {m['name']} ({m['id']})")
            break

    # Start collector (it will connect to Modbus on first cycle)
    await collector.start()

    # 8. Start scheduler for automatic reports
    scheduler = SchedulerService(db=db, influx_client=influx_client)
    await scheduler.start()

    # Ensure reports output directory exists
    reports_dir = settings.base_dir / settings.reports_output_dir
    reports_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Monitoreo PM8000 ready!")
    logger.info(f"  Modbus: {modbus_host}:{modbus_port} (unit {modbus_unit})")
    logger.info(f"  InfluxDB: {settings.influxdb_url}")
    logger.info(f"  Poll interval: {poll_interval}s")

    yield

    # Shutdown
    logger.info("Shutting down...")
    await scheduler.stop()
    await collector.stop()
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
