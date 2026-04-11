"""Async Modbus TCP client wrapper for PM8000."""

import asyncio
import logging
from typing import Any

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusIOException

from .register_map import RegisterBlock

logger = logging.getLogger(__name__)


class PM8000Client:
    """Async Modbus TCP client for reading PM8000 registers."""

    def __init__(
        self,
        host: str,
        port: int = 502,
        unit_id: int = 1,
        timeout: float = 3.0,
    ):
        self.host = host
        self.port = port
        self.unit_id = unit_id
        self.timeout = timeout
        self._client: AsyncModbusTcpClient | None = None
        self._connected = False
        self._lock = asyncio.Lock()

    @property
    def connected(self) -> bool:
        return self._connected and self._client is not None

    async def connect(self) -> bool:
        """Establish Modbus TCP connection."""
        async with self._lock:
            if self._connected and self._client:
                return True
            try:
                self._client = AsyncModbusTcpClient(
                    host=self.host,
                    port=self.port,
                    timeout=self.timeout,
                )
                connected = await self._client.connect()
                self._connected = connected
                if connected:
                    logger.info(f"Connected to PM8000 at {self.host}:{self.port}")
                else:
                    logger.warning(f"Failed to connect to {self.host}:{self.port}")
                return connected
            except Exception as e:
                logger.error(f"Connection error: {e}")
                self._connected = False
                return False

    async def disconnect(self):
        """Close Modbus TCP connection."""
        async with self._lock:
            if self._client:
                self._client.close()
                self._client = None
                self._connected = False
                logger.info("Disconnected from PM8000")

    async def read_block(self, block: RegisterBlock) -> list[int] | None:
        """Read a contiguous block of holding registers.

        Args:
            block: RegisterBlock defining start address and count

        Returns:
            List of 16-bit register values, or None on error
        """
        if not self._connected or not self._client:
            if not await self.connect():
                return None

        try:
            result = await self._client.read_holding_registers(
                address=block.start,
                count=block.count,
                slave=self.unit_id,
            )
            if result.isError():
                logger.warning(
                    f"Modbus error reading block '{block.name}' "
                    f"(addr={block.start}, count={block.count}): {result}"
                )
                return None
            return list(result.registers)
        except ModbusIOException as e:
            logger.error(f"Modbus IO error on block '{block.name}': {e}")
            self._connected = False
            return None
        except Exception as e:
            logger.error(f"Unexpected error reading block '{block.name}': {e}")
            self._connected = False
            return None

    async def read_all_blocks(
        self, blocks: list[RegisterBlock]
    ) -> dict[str, list[int]]:
        """Read all register blocks sequentially.

        Returns:
            Dict mapping block name to list of raw register values.
            Blocks that failed to read are omitted.
        """
        raw_data: dict[str, list[int]] = {}
        for block in blocks:
            result = await self.read_block(block)
            if result is not None:
                raw_data[block.name] = result
        return raw_data

    async def read_single(self, address: int, count: int = 2) -> list[int] | None:
        """Read a small number of registers at a specific address."""
        if not self._connected or not self._client:
            if not await self.connect():
                return None

        try:
            result = await self._client.read_holding_registers(
                address=address,
                count=count,
                slave=self.unit_id,
            )
            if result.isError():
                return None
            return list(result.registers)
        except Exception:
            self._connected = False
            return None
