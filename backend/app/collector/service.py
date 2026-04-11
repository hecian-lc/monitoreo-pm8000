"""Main data collection service - 1-second polling loop."""

import asyncio
import logging
import time
from typing import Any

from .broadcast import BroadcastManager
from .decoder import decode_registers
from .modbus_client import PM8000Client
from .register_map import RegisterMap
from .writer import InfluxWriter

logger = logging.getLogger(__name__)


class CollectorService:
    """Manages the PM8000 polling loop and data pipeline."""

    def __init__(
        self,
        modbus_client: PM8000Client,
        influx_writer: InfluxWriter,
        register_map: RegisterMap,
        broadcast: BroadcastManager,
        poll_interval: float = 1.0,
    ):
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
            "running": self._running,
            "connected": self._connected,
            "active_measurement_id": self._active_measurement_id,
            "poll_interval": self._poll_interval,
            "cycle_time_ms": round(self._cycle_time * 1000, 1),
            "total_cycles": self._total_cycles,
            "error_count": self._error_count,
            "ws_clients": self._broadcast.client_count,
        }

    def set_measurement(self, measurement_id: str | None):
        """Set the active measurement ID. Data is only stored when set."""
        self._active_measurement_id = measurement_id
        if measurement_id:
            logger.info(f"Active measurement: {measurement_id}")
        else:
            logger.info("Measurement stopped (no active measurement)")

    async def start(self):
        """Start the polling loop as a background task."""
        if self._running:
            logger.warning("Collector already running")
            return
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info(f"Collector started (interval={self._poll_interval}s)")

    async def stop(self):
        """Stop the polling loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        await self._modbus.disconnect()
        logger.info("Collector stopped")

    async def _poll_loop(self):
        """Main polling loop - reads all register blocks every interval."""
        reconnect_delay = 1.0
        max_reconnect_delay = 30.0

        while self._running:
            cycle_start = time.monotonic()

            try:
                # Ensure connected
                if not self._modbus.connected:
                    self._connected = False
                    await self._broadcast.broadcast_status(
                        "disconnected", "Connecting to PM8000..."
                    )
                    connected = await self._modbus.connect()
                    if not connected:
                        logger.warning(
                            f"Connection failed, retry in {reconnect_delay:.0f}s"
                        )
                        await asyncio.sleep(reconnect_delay)
                        reconnect_delay = min(
                            reconnect_delay * 2, max_reconnect_delay
                        )
                        continue
                    reconnect_delay = 1.0
                    self._connected = True
                    await self._broadcast.broadcast_status(
                        "connected", "Connected to PM8000"
                    )

                # Read all register blocks
                raw_data = await self._modbus.read_all_blocks(
                    self._register_map.blocks
                )

                if not raw_data:
                    self._connected = False
                    self._error_count += 1
                    await self._broadcast.broadcast(
                        {}, connected=False,
                        measurement_id=self._active_measurement_id,
                    )
                    continue

                # Decode raw registers to values
                readings = decode_registers(
                    self._register_map.blocks,
                    raw_data,
                    byte_order=self._register_map.byte_order,
                    word_order=self._register_map.word_order,
                )

                self._connected = True
                self._total_cycles += 1

                # Write to InfluxDB (only if measurement is active)
                if self._active_measurement_id:
                    await self._writer.write_readings(
                        readings,
                        measurement_id=self._active_measurement_id,
                    )

                # Broadcast to WebSocket clients (always, for live view)
                await self._broadcast.broadcast(
                    readings,
                    connected=True,
                    measurement_id=self._active_measurement_id,
                )

            except asyncio.CancelledError:
                raise
            except Exception as e:
                self._error_count += 1
                logger.error(f"Poll cycle error: {e}", exc_info=True)
                self._connected = False

            # Sleep for remaining interval
            elapsed = time.monotonic() - cycle_start
            self._cycle_time = elapsed
            sleep_time = max(0, self._poll_interval - elapsed)

            if elapsed > self._poll_interval:
                logger.warning(
                    f"Poll cycle took {elapsed*1000:.0f}ms "
                    f"(exceeds {self._poll_interval*1000:.0f}ms interval)"
                )

            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
