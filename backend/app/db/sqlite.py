"""SQLite database for devices, measurements, and report metadata."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import aiosqlite

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS devices (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    meter_model TEXT DEFAULT 'PM8000',
    host TEXT NOT NULL DEFAULT '192.168.1.100',
    port INTEGER DEFAULT 502,
    unit_id INTEGER DEFAULT 1,
    poll_interval REAL DEFAULT 1.0,
    register_map TEXT DEFAULT 'pm8000_default.yaml',
    byte_order TEXT DEFAULT 'big',
    word_order TEXT DEFAULT 'big',
    enabled INTEGER DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS measurements (
    id TEXT PRIMARY KEY,
    device_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    point_name TEXT DEFAULT 'T.G.',
    status TEXT DEFAULT 'idle',  -- idle, recording, stopped, compressed
    resolution TEXT DEFAULT '1s',
    created_at TEXT NOT NULL,
    started_at TEXT,
    stopped_at TEXT,
    compressed_at TEXT,
    FOREIGN KEY (device_id) REFERENCES devices(id)
);

CREATE TABLE IF NOT EXISTS reports (
    id TEXT PRIMARY KEY,
    measurement_id TEXT NOT NULL,
    name TEXT NOT NULL,
    status TEXT DEFAULT 'pending',  -- pending, generating, completed, error
    format TEXT DEFAULT 'docx',
    file_path TEXT,
    config_json TEXT,
    created_at TEXT NOT NULL,
    completed_at TEXT,
    error_message TEXT,
    FOREIGN KEY (measurement_id) REFERENCES measurements(id)
);

CREATE TABLE IF NOT EXISTS report_schedules (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    measurement_id TEXT,
    cron_expression TEXT NOT NULL,
    config_json TEXT NOT NULL,
    enabled INTEGER DEFAULT 1,
    last_run_at TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (measurement_id) REFERENCES measurements(id)
);

CREATE TABLE IF NOT EXISTS report_config (
    id INTEGER PRIMARY KEY DEFAULT 1,
    cliente TEXT DEFAULT '',
    num_informe TEXT DEFAULT '',
    atencion TEXT DEFAULT '',
    objetivo TEXT DEFAULT 'Conocer la potencia utilizada y disponible en el punto de medición.',
    equipo TEXT DEFAULT 'Schneider Electric PM8000.',
    periodicidad TEXT DEFAULT '1 segundo.',
    firma_nombre TEXT DEFAULT '',
    firma_cargo TEXT DEFAULT '',
    fuente TEXT DEFAULT 'Century Gothic',
    color_principal TEXT DEFAULT '#202E6B',
    color_encabezado_tabla TEXT DEFAULT '#DDEBF7',
    color_fase_r TEXT DEFAULT '#E74C3C',
    color_fase_s TEXT DEFAULT '#3498DB',
    color_fase_t TEXT DEFAULT '#2ECC71',
    color_trif TEXT DEFAULT '#8E44AD',
    img_portada TEXT DEFAULT '',
    img_encabezado TEXT DEFAULT '',
    img_pie TEXT DEFAULT '',
    gemini_api_key TEXT DEFAULT ''
);
"""


class Database:
    """Async SQLite database manager."""

    def __init__(self, db_path: str):
        self._path = db_path
        self._db: aiosqlite.Connection | None = None

    async def connect(self):
        Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        self._db = await aiosqlite.connect(self._path)
        self._db.row_factory = aiosqlite.Row
        await self._db.executescript(SCHEMA)
        await self._db.commit()
        # Insert default report config if not exists
        async with self._db.execute("SELECT COUNT(*) FROM report_config") as cur:
            row = await cur.fetchone()
            if row[0] == 0:
                await self._db.execute("INSERT INTO report_config DEFAULT VALUES")
                await self._db.commit()
        logger.info(f"SQLite database ready: {self._path}")

    async def close(self):
        if self._db:
            await self._db.close()
            self._db = None

    # ─── Devices ───

    async def create_device(
        self, id: str, name: str, meter_model: str = "PM8000",
        host: str = "192.168.1.100",
        port: int = 502, unit_id: int = 1, poll_interval: float = 1.0,
        register_map: str = "pm8000_default.yaml",
        byte_order: str = "big", word_order: str = "big",
    ) -> dict:
        now = datetime.utcnow().isoformat()
        await self._db.execute(
            "INSERT INTO devices (id, name, meter_model, host, port, unit_id, poll_interval, register_map, byte_order, word_order, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (id, name, meter_model, host, port, unit_id, poll_interval, register_map, byte_order, word_order, now),
        )
        await self._db.commit()
        return await self.get_device(id)

    async def get_device(self, id: str) -> dict | None:
        async with self._db.execute("SELECT * FROM devices WHERE id = ?", (id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None

    async def list_devices(self) -> list[dict]:
        async with self._db.execute("SELECT * FROM devices ORDER BY created_at DESC") as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def update_device(self, id: str, **kwargs):
        if not kwargs:
            return
        sets = [f"{k} = ?" for k in kwargs]
        vals = list(kwargs.values())
        vals.append(id)
        await self._db.execute(
            f"UPDATE devices SET {', '.join(sets)} WHERE id = ?", vals,
        )
        await self._db.commit()

    async def delete_device(self, id: str):
        # Delete related measurements and their reports
        async with self._db.execute(
            "SELECT id FROM measurements WHERE device_id = ?", (id,)
        ) as cur:
            rows = await cur.fetchall()
            for row in rows:
                await self._db.execute("DELETE FROM reports WHERE measurement_id = ?", (row["id"],))
        await self._db.execute("DELETE FROM measurements WHERE device_id = ?", (id,))
        await self._db.execute("DELETE FROM devices WHERE id = ?", (id,))
        await self._db.commit()

    # ─── Measurements ───

    async def create_measurement(
        self, id: str, device_id: str, name: str,
        description: str = "", point_name: str = "T.G.",
    ) -> dict:
        now = datetime.utcnow().isoformat()
        await self._db.execute(
            "INSERT INTO measurements (id, device_id, name, description, point_name, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (id, device_id, name, description, point_name, now),
        )
        await self._db.commit()
        return await self.get_measurement(id)

    async def get_measurement(self, id: str) -> dict | None:
        async with self._db.execute("SELECT * FROM measurements WHERE id = ?", (id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None

    async def list_measurements(self, device_id: str | None = None) -> list[dict]:
        if device_id:
            sql = "SELECT * FROM measurements WHERE device_id = ? ORDER BY created_at DESC"
            args = (device_id,)
        else:
            sql = "SELECT * FROM measurements ORDER BY created_at DESC"
            args = ()
        async with self._db.execute(sql, args) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def update_measurement_status(self, id: str, status: str, **kwargs):
        sets = ["status = ?"]
        vals = [status]
        for k, v in kwargs.items():
            sets.append(f"{k} = ?")
            vals.append(v)
        vals.append(id)
        await self._db.execute(
            f"UPDATE measurements SET {', '.join(sets)} WHERE id = ?", vals,
        )
        await self._db.commit()

    async def delete_measurement(self, id: str):
        await self._db.execute("DELETE FROM reports WHERE measurement_id = ?", (id,))
        await self._db.execute("DELETE FROM measurements WHERE id = ?", (id,))
        await self._db.commit()

    # ─── Report Config ───

    async def get_report_config(self) -> dict:
        async with self._db.execute("SELECT * FROM report_config WHERE id = 1") as cur:
            row = await cur.fetchone()
            return dict(row) if row else {}

    async def update_report_config(self, **kwargs):
        if not kwargs:
            return
        sets = [f"{k} = ?" for k in kwargs]
        vals = list(kwargs.values())
        await self._db.execute(
            f"UPDATE report_config SET {', '.join(sets)} WHERE id = 1", vals,
        )
        await self._db.commit()

    # ─── Reports ───

    async def create_report(
        self, id: str, measurement_id: str, name: str,
        format: str = "docx", config: dict | None = None,
    ) -> dict:
        now = datetime.utcnow().isoformat()
        config_json = json.dumps(config or {})
        await self._db.execute(
            "INSERT INTO reports (id, measurement_id, name, format, config_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (id, measurement_id, name, format, config_json, now),
        )
        await self._db.commit()
        return await self.get_report(id)

    async def get_report(self, id: str) -> dict | None:
        async with self._db.execute("SELECT * FROM reports WHERE id = ?", (id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None

    async def list_reports(self, measurement_id: str | None = None) -> list[dict]:
        if measurement_id:
            sql = "SELECT * FROM reports WHERE measurement_id = ? ORDER BY created_at DESC"
            args = (measurement_id,)
        else:
            sql = "SELECT * FROM reports ORDER BY created_at DESC"
            args = ()
        async with self._db.execute(sql, args) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def update_report(self, id: str, **kwargs):
        if not kwargs:
            return
        sets = [f"{k} = ?" for k in kwargs]
        vals = list(kwargs.values())
        vals.append(id)
        await self._db.execute(
            f"UPDATE reports SET {', '.join(sets)} WHERE id = ?", vals,
        )
        await self._db.commit()

    # ─── Report Schedules ───

    async def create_schedule(
        self, id: str, name: str, cron_expression: str,
        config: dict, measurement_id: str | None = None,
    ) -> dict:
        now = datetime.utcnow().isoformat()
        config_json = json.dumps(config)
        await self._db.execute(
            "INSERT INTO report_schedules (id, name, measurement_id, cron_expression, config_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (id, name, measurement_id, cron_expression, config_json, now),
        )
        await self._db.commit()
        async with self._db.execute("SELECT * FROM report_schedules WHERE id = ?", (id,)) as cur:
            row = await cur.fetchone()
            return dict(row)

    async def list_schedules(self) -> list[dict]:
        async with self._db.execute("SELECT * FROM report_schedules ORDER BY created_at DESC") as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def update_schedule(self, id: str, **kwargs):
        if not kwargs:
            return
        sets = [f"{k} = ?" for k in kwargs]
        vals = list(kwargs.values())
        vals.append(id)
        await self._db.execute(
            f"UPDATE report_schedules SET {', '.join(sets)} WHERE id = ?", vals,
        )
        await self._db.commit()

    async def delete_schedule(self, id: str):
        await self._db.execute("DELETE FROM report_schedules WHERE id = ?", (id,))
        await self._db.commit()
