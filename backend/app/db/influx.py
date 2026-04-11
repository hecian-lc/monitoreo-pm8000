"""InfluxDB client setup, bucket creation, and query helpers."""

import logging
from datetime import datetime

from influxdb_client import BucketRetentionRules, TaskCreateRequest
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync

from ..config import settings

logger = logging.getLogger(__name__)

# Bucket configurations: name, retention (seconds, 0=infinite)
BUCKETS = {
    settings.influxdb_bucket: 30 * 24 * 3600,        # pm_raw: 30 days
    settings.influxdb_bucket_1min: 365 * 24 * 3600,   # pm_1min: 1 year
    settings.influxdb_bucket_15min: 5 * 365 * 24 * 3600,  # pm_15min: 5 years
    settings.influxdb_bucket_1hour: 0,                 # pm_1hour: infinite
}


async def create_influx_client() -> InfluxDBClientAsync:
    """Create and return an async InfluxDB client."""
    client = InfluxDBClientAsync(
        url=settings.influxdb_url,
        token=settings.influxdb_token,
        org=settings.influxdb_org,
    )
    return client


async def setup_buckets(client: InfluxDBClientAsync):
    """Create InfluxDB buckets if they don't exist."""
    buckets_api = client.buckets_api()
    org_api = client.organizations_api()

    orgs = await org_api.find_organizations(org=settings.influxdb_org)
    if not orgs:
        logger.error(f"Organization '{settings.influxdb_org}' not found")
        return
    org_id = orgs[0].id

    existing = await buckets_api.find_buckets()
    existing_names = {b.name for b in existing.buckets} if existing.buckets else set()

    for bucket_name, retention_secs in BUCKETS.items():
        if bucket_name in existing_names:
            logger.info(f"Bucket '{bucket_name}' already exists")
            continue
        try:
            rules = BucketRetentionRules(
                type="expire",
                every_seconds=retention_secs,
            ) if retention_secs > 0 else BucketRetentionRules(
                type="expire",
                every_seconds=0,
            )
            await buckets_api.create_bucket(
                bucket_name=bucket_name,
                retention_rules=rules,
                org_id=org_id,
            )
            logger.info(f"Created bucket '{bucket_name}' (retention={retention_secs}s)")
        except Exception as e:
            logger.warning(f"Could not create bucket '{bucket_name}': {e}")


async def setup_downsampling_tasks(client: InfluxDBClientAsync):
    """Create InfluxDB downsampling tasks."""
    tasks_api = client.tasks_api()
    org = settings.influxdb_org

    # Task 1: Raw -> 1min (runs every minute)
    task_1min_flux = f'''
option task = {{name: "downsample_1min", every: 1m}}

from(bucket: "{settings.influxdb_bucket}")
    |> range(start: -2m)
    |> filter(fn: (r) => r._measurement == "power_metrics")
    |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
    |> to(bucket: "{settings.influxdb_bucket_1min}", org: "{org}")
'''

    # Task 2: 1min -> 15min (runs every 15 minutes)
    task_15min_flux = f'''
option task = {{name: "downsample_15min", every: 15m}}

from(bucket: "{settings.influxdb_bucket_1min}")
    |> range(start: -30m)
    |> filter(fn: (r) => r._measurement == "power_metrics")
    |> aggregateWindow(every: 15m, fn: mean, createEmpty: false)
    |> to(bucket: "{settings.influxdb_bucket_15min}", org: "{org}")
'''

    # Task 3: 15min -> 1hour (runs every hour)
    task_1hour_flux = f'''
option task = {{name: "downsample_1hour", every: 1h}}

from(bucket: "{settings.influxdb_bucket_15min}")
    |> range(start: -2h)
    |> filter(fn: (r) => r._measurement == "power_metrics")
    |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
    |> to(bucket: "{settings.influxdb_bucket_1hour}", org: "{org}")
'''

    tasks_to_create = [
        ("downsample_1min", task_1min_flux),
        ("downsample_15min", task_15min_flux),
        ("downsample_1hour", task_1hour_flux),
    ]

    try:
        existing_tasks = await tasks_api.find_tasks()
        existing_names = {t.name for t in existing_tasks}
    except Exception:
        existing_names = set()

    for task_name, flux in tasks_to_create:
        if task_name in existing_names:
            logger.info(f"Downsampling task '{task_name}' already exists")
            continue
        try:
            await tasks_api.create_task(
                TaskCreateRequest(
                    flux=flux,
                    org=org,
                    status="active",
                )
            )
            logger.info(f"Created downsampling task '{task_name}'")
        except Exception as e:
            logger.warning(f"Could not create task '{task_name}': {e}")
