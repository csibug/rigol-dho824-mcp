"""
multimeter2.py - digital voltmeter (dvm) and hardware counter tools.
optimized for tape deck speed calibration and audio level monitoring.
"""

import asyncio
import time
from enum import Enum
from typing import Optional, TypedDict

from .common2 import ChannelNumber


class DVMMode(str, Enum):
    AC_RMS = "ACRM"
    DC = "DC"
    AC_DC_RMS = "DCRM"

class CounterMode(str, Enum):
    FREQUENCY = "FREQuency"
    PERIOD = "PERiod"
    TOTALIZE = "TOTalize"

class DVMResult(TypedDict):
    """detailed output from the digital voltmeter."""
    enabled: bool
    source: str
    mode: str
    reading: float
    unit: str

class CounterResult(TypedDict):
    """high-precision frequency or period measurement."""
    enabled: bool
    source: str
    mode: str
    value: float
    unit: str

# === LOGIC (synchronous hardware interaction) ===

def _sync_configure_dvm(scope, channel: int, mode: DVMMode, enabled: bool) -> DVMResult:
    """configures the dvm and ensures hardware/gui stability before reading."""
    instr = scope.connect()

    instr.write(f":DVM:SOURce CHANnel{channel}")
    instr.write(f":DVM:MODE {mode.value}")
    instr.write(f":DVM:ENABle {'ON' if enabled else 'OFF'}")

    reading = 0.0
    if enabled:
        # allow time for the dvm window to initialize and capture the first sample
        time.sleep(2)

        # polling loop for a valid reading (skipping the 9.9e37 error constant)
        for _ in range(3):
            try:
                raw = instr.query(":DVM:CURRent?").strip()
                val = float(raw)
                if 0.0 <= val < 1e30:
                    reading = val
                    break
            except Exception:
                pass
            time.sleep(0.3)

    return {
        "enabled": enabled,
        "source": f"CH{channel}",
        "mode": mode.name,
        "reading": reading,
        "unit": "V"
    }

def _sync_get_counter(scope, channel: Optional[int] = None, mode: Optional[CounterMode] = None) -> CounterResult:
    """reads the 7-digit hardware counter with a robust warm-up for the gate cycle."""
    instr = scope.connect()

    if channel is not None:
        instr.write(f":COUNter:SOURce CHANnel{channel}")
    if mode is not None:
        instr.write(f":COUNter:MODE {mode.value}")

    # ensure counter is active; the dho824 requires time for the first gate cycle
    is_enabled = instr.query(":COUNter:ENABle?").strip() == "1"
    if not is_enabled:
        instr.write(":COUNter:ENABle ON")
        time.sleep(1.5) # critical wake-up time for the first measurement
    else:
        time.sleep(0.2)

    val = 0.0
    for _ in range(5):
        try:
            raw_res = instr.query(":COUNter:CURRent?").strip()
            f_val = float(raw_res)
            # validate range and skip the 9.9e37 overflow value
            if 0.0 < f_val < 1e30:
                val = f_val
                break
        except Exception:
            pass
        time.sleep(0.5)

    current_mode = instr.query(":COUNter:MODE?").strip()
    source = instr.query(":COUNter:SOURce?").strip()

    # map units based on the active counter mode
    unit_map = {"FREQ": "Hz", "PER": "s", "TOT": "counts"}
    unit = unit_map.get(current_mode[:4].upper(), "")

    return {
        "enabled": True,
        "source": source,
        "mode": current_mode,
        "value": val,
        "unit": unit
    }

# === MCP TOOLS ===

def register_multimeter_tools(mcp, scope):
    """registers dvm and counter tools with the mcp server."""

    @mcp.tool()
    async def get_dvm_reading(
        channel: ChannelNumber = ChannelNumber.CH1,
        mode: DVMMode = DVMMode.AC_RMS
    ) -> DVMResult:
        """
        reads the digital voltmeter.
        use ac_rms for sony deck output levels and dc for checking power rails.
        """
        return await asyncio.to_thread(_sync_configure_dvm, scope, channel.value, mode, True)

    @mcp.tool()
    async def get_high_res_frequency(
        channel: ChannelNumber = ChannelNumber.CH1
    ) -> CounterResult:
        """
        fetches 7-digit frequency data using the dedicated hardware counter.
        perfect for sony tc-fx44 speed calibration (3000hz/3150hz target).
        """
        return await asyncio.to_thread(_sync_get_counter, scope, channel.value, CounterMode.FREQUENCY)

    @mcp.tool()
    async def reset_counter_totalize() -> str:
        """
        safely resets the counter. ensures it is active before sending the clear command.
        """
        def _work():
            instr = scope.connect()
            # 1. verify activation to prevent clearing errors
            is_enabled = instr.query(":COUNter:ENABle?").strip() == "1"
            if not is_enabled:
                instr.write(":COUNter:ENABle ON")
                time.sleep(0.5) # hardware settling time

            # 2. execute clear
            instr.write(":COUNter:TOTalize:CLEar")
            return "counter enabled and reset to zero."

        return await asyncio.to_thread(_work)
