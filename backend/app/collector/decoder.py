"""Decode raw Modbus register values to Python floats/ints."""

import struct
from typing import Any

from .register_map import Register, RegisterBlock


def decode_float32(
    registers: list[int],
    byte_order: str = "big",
    word_order: str = "big",
) -> float:
    """Decode two 16-bit registers into a IEEE 754 float32.

    Args:
        registers: Two consecutive 16-bit register values [high, low] or [low, high]
        byte_order: "big" (ABCD) or "little" (DCBA)
        word_order: "big" (high word first) or "little" (low word first)
    """
    if len(registers) < 2:
        return float("nan")

    r0, r1 = registers[0], registers[1]

    # Word order: which register comes first
    if word_order == "big":
        high, low = r0, r1
    else:
        high, low = r1, r0

    # Pack as two unsigned 16-bit values
    raw = struct.pack(">HH", high, low)

    # Byte order adjustment
    if byte_order == "big":
        # ABCD - already correct
        pass
    elif byte_order == "little":
        # DCBA
        raw = raw[::-1]
    elif byte_order == "swap":
        # CDAB (word swap)
        raw = raw[2:4] + raw[0:2]

    value = struct.unpack(">f", raw)[0]

    # Sanity check for NaN / Inf
    if not (-1e15 < value < 1e15):
        return float("nan")

    return value


def decode_int16(register: int) -> int:
    """Decode a single 16-bit register as signed integer."""
    if register > 32767:
        return register - 65536
    return register


def decode_block(
    block: RegisterBlock,
    raw_registers: list[int],
    byte_order: str = "big",
    word_order: str = "big",
) -> dict[str, Any]:
    """Decode all registers in a block from raw Modbus response.

    Args:
        block: RegisterBlock with register definitions
        raw_registers: List of 16-bit values from Modbus read
        byte_order: Float32 byte order
        word_order: Float32 word order

    Returns:
        Dict mapping register name to decoded value
    """
    readings: dict[str, Any] = {}

    for reg in block.registers:
        # Calculate offset within the raw registers array
        offset = reg.address - block.start
        if offset < 0 or offset + 1 >= len(raw_registers):
            continue

        if reg.type == "float32":
            value = decode_float32(
                raw_registers[offset : offset + 2],
                byte_order=byte_order,
                word_order=word_order,
            )
        elif reg.type == "int16":
            value = decode_int16(raw_registers[offset])
        else:
            continue

        readings[reg.name] = value

    return readings


def decode_registers(
    blocks: list[RegisterBlock],
    raw_data: dict[str, list[int]],
    byte_order: str = "big",
    word_order: str = "big",
) -> dict[str, Any]:
    """Decode all blocks from raw Modbus data.

    Args:
        blocks: List of RegisterBlocks
        raw_data: Dict mapping block name to raw register values
        byte_order: Float32 byte order
        word_order: Float32 word order

    Returns:
        Dict mapping register name to decoded value
    """
    readings: dict[str, Any] = {}
    for block in blocks:
        if block.name in raw_data:
            block_readings = decode_block(
                block, raw_data[block.name], byte_order, word_order
            )
            readings.update(block_readings)
    return readings
