"""APScheduler integration for scheduled report generation."""

import json
import logging
import uuid
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from ..config import settings
from ..db.sqlite import Database
from ..reports.generator import generate_report

logger = logging.getLogger(__name__)


class SchedulerService:
    """Manages cron-based scheduled report generation."""

    def __init__(self, db: Database, influx_client):
        self._db = db
        self._influx = influx_client
        self._scheduler = AsyncIOScheduler()

    async def start(self):
        """Start the scheduler and load saved jobs."""
        self._scheduler.start()
        await self._load_jobs()
        logger.info("Scheduler started")

    async def stop(self):
        """Shutdown the scheduler."""
        self._scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")

    async def _load_jobs(self):
        """Load all enabled schedules from DB and register them."""
        schedules = await self._db.list_schedules()
        for s in schedules:
            if s.get("enabled"):
                self._add_job(s)

    def _add_job(self, schedule: dict):
        """Add a single schedule to APScheduler."""
        schedule_id = schedule["id"]
        cron_expr = schedule["cron_expression"]

        try:
            parts = cron_expr.strip().split()
            if len(parts) != 5:
                logger.warning(f"Invalid cron expression for schedule {schedule_id}: {cron_expr}")
                return

            trigger = CronTrigger(
                minute=parts[0],
                hour=parts[1],
                day=parts[2],
                month=parts[3],
                day_of_week=parts[4],
            )

            self._scheduler.add_job(
                self._run_scheduled_report,
                trigger=trigger,
                id=schedule_id,
                name=schedule.get("name", schedule_id),
                kwargs={"schedule_id": schedule_id},
                replace_existing=True,
            )
            logger.info(f"Scheduled report '{schedule.get('name')}' ({cron_expr})")

        except Exception as e:
            logger.error(f"Failed to add schedule {schedule_id}: {e}")

    async def _run_scheduled_report(self, schedule_id: str):
        """Execute a scheduled report generation."""
        logger.info(f"Running scheduled report: {schedule_id}")

        schedule = None
        for s in await self._db.list_schedules():
            if s["id"] == schedule_id:
                schedule = s
                break

        if not schedule:
            logger.warning(f"Schedule {schedule_id} not found")
            return

        config = json.loads(schedule.get("config_json", "{}"))
        measurement_id = schedule.get("measurement_id") or config.get("measurement_id")

        if not measurement_id:
            logger.warning(f"No measurement_id for schedule {schedule_id}")
            return

        report_id = str(uuid.uuid4())[:8]
        report_name = f"Auto - {schedule.get('name', '')} - {datetime.now().strftime('%d/%m/%Y')}"

        await self._db.create_report(
            id=report_id,
            measurement_id=measurement_id,
            name=report_name,
            format=config.get("format", "docx"),
            config=config,
        )

        await generate_report(
            report_id=report_id,
            measurement_id=measurement_id,
            influx_client=self._influx,
            db=self._db,
            report_config_overrides=config,
        )

        await self._db.update_schedule(
            schedule_id,
            last_run_at=datetime.utcnow().isoformat(),
        )

    async def add_schedule(self, schedule: dict):
        """Add a new schedule (called when user creates one via API)."""
        self._add_job(schedule)

    async def remove_schedule(self, schedule_id: str):
        """Remove a schedule."""
        try:
            self._scheduler.remove_job(schedule_id)
        except Exception:
            pass

    async def update_schedule(self, schedule: dict):
        """Update an existing schedule."""
        schedule_id = schedule["id"]
        try:
            self._scheduler.remove_job(schedule_id)
        except Exception:
            pass
        if schedule.get("enabled"):
            self._add_job(schedule)
