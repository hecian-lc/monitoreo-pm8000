"""Load and parse PM8000 Modbus register map from YAML."""

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class Register:
    name: str
    address: int
    type: str  # "float32", "int16", etc.
    unit: str
    phase: str
    category: str
    description: str


@dataclass
class RegisterBlock:
    name: str
    start: int
    count: int
    description: str
    registers: list[Register] = field(default_factory=list)


@dataclass
class RegisterMap:
    device_name: str
    manufacturer: str
    default_port: int
    default_unit_id: int
    byte_order: str
    word_order: str
    blocks: list[RegisterBlock]
    registers: list[Register]
    _by_address: dict[int, Register] = field(default_factory=dict, repr=False)

    def __post_init__(self):
        self._by_address = {r.address: r for r in self.registers}
        # Assign registers to their blocks
        for block in self.blocks:
            block_end = block.start + block.count * 2
            block.registers = [
                r for r in self.registers
                if block.start <= r.address < block_end
            ]

    def get_register(self, address: int) -> Register | None:
        return self._by_address.get(address)

    def get_by_category(self, category: str) -> list[Register]:
        return [r for r in self.registers if r.category == category]

    def get_by_name(self, name: str) -> Register | None:
        for r in self.registers:
            if r.name == name:
                return r
        return None


def load_register_map(path: str | Path) -> RegisterMap:
    """Load register map from YAML file."""
    path = Path(path)
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    device = data["device"]
    blocks = [
        RegisterBlock(
            name=b["name"],
            start=b["start"],
            count=b["count"],
            description=b["description"],
        )
        for b in data.get("blocks", [])
    ]
    registers = [
        Register(
            name=r["name"],
            address=r["address"],
            type=r["type"],
            unit=r["unit"],
            phase=r["phase"],
            category=r["category"],
            description=r["description"],
        )
        for r in data.get("registers", [])
    ]

    return RegisterMap(
        device_name=device["name"],
        manufacturer=device["manufacturer"],
        default_port=device["default_port"],
        default_unit_id=device["default_unit_id"],
        byte_order=device["byte_order"],
        word_order=device["word_order"],
        blocks=blocks,
        registers=registers,
    )
