"""Data collection services - per-device polling + multi-device manager."""

import asyncio
import logging
import time
from pathlib import Path
from typing import Any

from .broadcast import BroadcastManager
from .decoder import decode_registers
from .modbus_client import PM8000Client
from .register_map import RegisterMap, load_register_map
from .writer import InfluxWriter

logger = logging.getLogger(__name__)


class CollectorService:
    """Manages a single PM8000 polling loop."""

    def __init__(
        self,
        device_id: str,
        modbus_client: PM8000Client,
        influx_writer: InfluxWriter,
        register_map: RegisterMap,
        broadcast: BroadcastManager,
        poll_interval: float = 1.0,
    ):
        self._device_id = device_id
        self._modbus = modbus_client
        self._writer = influx_writer
        self._register_map = register_map
        self._broadcast = broadcast
        self._poll_interval = poll_interval
        self._running = False
        self._task: asyncio.Task | None = None
        self._active_measurement_id: str | None = None
        self._connected = False
        self._cycle_time: float = 0.0
        self._total_cycles: int = 0
        self._error_count: int = 0

    @property
    def device_id(self) -> str:
        return self._device_id

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def active_measurement_id(self) -> str | None:
        return self._active_measurement_id

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "device_id": self._device_id,
            "running": self._running,
            "connected": self._connected,
            "active_measurement_id": self._active_measurement_id,
            "poll_interval": self._poll_interval,
            "cycle_time_ms": round(self._cycle_time * 1000, 1),
            "total_cycles": self._total_cycles,
            "error_count": self._error_count,
        }

    def set_measurement(self, measurement_id: str | None):
        self._active_measurement_id = measurement_id
        if measurement_id:
            logger.info(f"[{self._device_id}] Active measurement: {measurement_id}")
        else:
            logger.info(f"[{self._device_id}] Measurement stopped")

    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info(f"[{self._device_id}] Collector started (interval={self._poll_interval}s)")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        await self._modbus.disconnect()
        logger.info(f"[{self._device_id}] Collector stopped")

    async def _poll_loop(self):
        reconnect_delay = 1.0
        max_reconnect_delay = 30.0

        while self._running:
            cycle_start = time.monotonic()

            try:
                if not self._modbus.connected:
                    self._connected = False
                    connected = await self._modbus.connect()
                    if not connected:
                        await asyncio.sleep(reconnect_delay)
                        reconnect_delay = min(reconnect_delay * 2, max_reconnect_delay)
                        continue
                    reconnect_delay = 1.0
                    self._connected = True

                raw_data = await self._modbus.read_all_blocks(self._register_map.blocks)

                if not raw_data:
                    self._connected = False
                    self._error_count += 1
                    await self._broadcast.broadcast(
                        {}, connected=False,
                        device_id=self._device_id,
                        measurement_id=self._active_measurement_id,
                    )
                    continue

                readings = decode_registers(
                    self._register_map.blocks, raw_data,
                    byte_order=self._register_map.byte_order,
                    word_order=self._register_map.word_order,
                )

                self._connected = True
                self._total_cycles += 1

                if self._active_measurement_id:
                    await self._writer.write_readings(
                        readings,
                        measurement_id=self._active_measurement_id,
                        device_id=self._device_id,
                    )

                await self._broadcast.broadcast(
                    readings, connected=True,
                    device_id=self._device_id,
                    measurement_id=self._active_measurement_id,
                )

            except asyncio.CancelledError:
                raise
            except Exception as e:
                self._error_count += 1
                logger.error(f"[{self._device_id}] Poll error: {e}", exc_info=True)
                self._connected = False

            elapsed = time.monotonic() - cycle_start
            self._cycle_time = elapsed
            sleep_time = max(0, self._poll_interval - elapsed)
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)


class CollectorManager:
    """Manages multiple CollectorService instances, one per device."""

    def __init__(
        self,
        influx_writer: InfluxWriter,
        broadcast: BroadcastManager,
        register_maps_dir: Path,
    ):
        self._writer = influx_writer
        self._broadcast = broadcast
        self._maps_dir = register_maps_dir
        self._collectors: dict[str, CollectorService] = {}
        self._register_maps: dict[str, RegisterMap] = {}

    @property
    def collectors(self) -> dict[str, CollectorService]:
        return self._collectors

    def get_collector(self, device_id: str) -> CollectorService | None:
        return self._collectors.get(device_id)

    def _load_register_map(self, map_name: str) -> RegisterMap:
        if map_name not in self._register_maps:
            path = self._maps_dir / map_name
            self._register_maps[map_name] = load_register_map(path)
        return self._register_maps[map_name]

    async def add_device(self, device: dict):
        """Create and start a collector for a device."""
        device_id = device["id"]
        if device_id in self._collectors:
            await self.remove_device(device_id)

        register_map = self._load_register_map(device.get("register_map", "pm8000_default.yaml"))
        modbus_client = PM8000Client(
            host=device["host"],
            port=device["port"],
            unit_id=device["unit_id"],
        )
        collector = CollectorService(
            device_id=device_id,
            modbus_client=modbus_client,
            influx_writer=self._writer,
            register_map=register_map,
            broadcast=self._broadcast,
            poll_interval=device.get("poll_interval", 1.0),
        )
        self._collectors[device_id] = collector

        if device.get("enabled", 1):
            await collector.start()

        logger.info(f"Device '{device.get('name')}' ({device_id}) added to collector manager")

    async def remove_device(self, device_id: str):
        """Stop and remove a collector."""
        collector = self._collectors.pop(device_id, None)
        if collector:
            await collector.stop()
            logger.info(f"Device {device_id} removed from collector manager")

    async def update_device(self, device: dict):
        """Restart collector with updated config."""
        await self.add_device(device)  # add_device handles remove if exists

    async def stop_all(self):
        """Stop all collectors."""
        for collector in self._collectors.values():
            await collector.stop()
        self._collectors.clear()

    def get_all_stats(self) -> list[dict]:
        return [c.stats for c in self._collectors.values()]

    async def test_connection(self, host: str, port: int, unit_id: int) -> bool:
        """Test Modbus TCP connection to a device."""
        client = PM8000Client(host=host, port=port, unit_id=unit_id, timeout=5.0)
        try:
            connected = await client.connect()
            if connected:
                await client.disconnect()
            return connected
        except Exception:
            return False
