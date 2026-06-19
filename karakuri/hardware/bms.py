"""BMS telemetry helpers for the 8S LiFePO4 power pack."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

MIN_PACK_VOLTAGE_V = 21.8
MAX_CELL_SPREAD_V = 0.08
MAX_PACK_TEMP_C = 55.0


@dataclass(frozen=True)
class BmsSample:
    pack_voltage_v: float
    pack_current_a: float
    state_of_charge_pct: float
    cell_voltages_v: tuple[float, ...]
    temperatures_c: tuple[float, ...]
    fault: str | None = None

    @property
    def cell_count(self) -> int:
        return len(self.cell_voltages_v)

    @property
    def cell_spread_v(self) -> float:
        if not self.cell_voltages_v:
            return 0.0
        return max(self.cell_voltages_v) - min(self.cell_voltages_v)

    @property
    def max_temp_c(self) -> float:
        if not self.temperatures_c:
            return 0.0
        return max(self.temperatures_c)


def _float_tuple(values: Any) -> tuple[float, ...]:
    if values is None:
        return ()
    if not isinstance(values, list | tuple):
        raise ValueError("expected a list of numeric values")
    return tuple(float(value) for value in values)


def parse_bms_json(payload: str | bytes | dict[str, Any]) -> BmsSample:
    data = json.loads(payload) if isinstance(payload, str | bytes) else payload
    return BmsSample(
        pack_voltage_v=float(data["pack_voltage_v"]),
        pack_current_a=float(data.get("pack_current_a", 0.0)),
        state_of_charge_pct=float(data.get("state_of_charge_pct", 0.0)),
        cell_voltages_v=_float_tuple(data.get("cell_voltages_v")),
        temperatures_c=_float_tuple(data.get("temperatures_c")),
        fault=data.get("fault"),
    )


def evaluate_bms(sample: BmsSample) -> list[str]:
    faults: list[str] = []
    if sample.fault:
        faults.append(f"BMS_FAULT:{sample.fault}")
    if sample.pack_voltage_v < MIN_PACK_VOLTAGE_V:
        faults.append("ERR_VOLT_DROP_01")
    if sample.cell_count != 8:
        faults.append("ERR_BMS_CELL_COUNT")
    if sample.cell_spread_v > MAX_CELL_SPREAD_V:
        faults.append("ERR_BMS_CELL_SPREAD")
    if sample.max_temp_c > MAX_PACK_TEMP_C:
        faults.append("ERR_BMS_TEMP")
    return faults
