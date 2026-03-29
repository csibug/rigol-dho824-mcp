"""
measure2.py - automated measurement tools for level and frequency analysis.
essential for sony tc-fx44 calibration (speed, level, and distortion).
"""

import asyncio
import time
from enum import Enum
from typing import List, Optional

from .common2 import ChannelNumber

# === ENUMS & CONSTANTS ===

class MeasureItem(str, Enum):
    """supported measurement types on the rigol dho824."""
    VPP  = "VPP"
    VMAX = "VMAX"
    VMIN = "VMIN"
    VAVG = "VAVG"
    VRMS = "VRMS"
    FREQ = "FREQ"
    PERI = "PERI"

# rigol invalid data threshold (9.9e37) - returned when signal is unstable
_INVALID_LIMIT = 9.0e37

def _parse_measure_val(raw_str: str) -> Optional[float]:
    """cleans and validates raw measurement data from the scope."""
    try:
        clean = raw_str.strip().replace('"', '')
        val = float(clean)
        return val if abs(val) < _INVALID_LIMIT else None
    except (ValueError, TypeError):
        return None

# === LOGIC (synchronous hardware interaction) ===

def _sync_get_metrics(scope, channel: int, items: List[MeasureItem]):
    """
    fetches measurements with a retry loop to allow hardware
    calculation time. activates items on screen for visual feedback.
    """
    instr = scope.connect()
    results = {}

    for item in items:
        # enable measurement on the display
        instr.write(f":MEASure:ITEM {item.value},CHANnel{channel}")

        # polling loop: allow up to 1 second for the hardware to stabilize
        final_val = None
        for _ in range(5):
            raw = instr.query(f":MEASure:ITEM? {item.value},CHANnel{channel}")
            final_val = _parse_measure_val(raw)
            if final_val is not None:
                break
            time.sleep(0.2)

        results[item.value] = final_val

    return results

def _sync_clear_measurements(scope) -> str:
    """
    executes measurement clear and flushes the system error buffer.
    using parameter-less :CLEar to avoid firmware command errors.
    """
    instr = scope.connect()
    instr.write(":MEASure:CLEar")

    # read and flush errors to ensure a clean state
    raw_error = instr.query(":SYSTem:ERRor?").strip()
    instr.query(":SYSTem:ERRor?")

    return f"clear completed. last status: {raw_error}"

# === MCP TOOLS ===

def register_measure_tools(mcp, scope):
    """registers measurement-related tools with the mcp server."""

    @mcp.tool()
    async def get_metrics(
        channel: ChannelNumber = ChannelNumber.CH1,
        items: Optional[List[MeasureItem]] = None
    ) -> str:
        """
        fetches requested metrics (vpp, frequency, vrms) from a channel.
        critical for monitoring tape speed and output levels (0vu).
        """
        # default items if none provided
        query_items = items if items else [MeasureItem.VPP, MeasureItem.FREQ, MeasureItem.VRMS]

        res = await asyncio.to_thread(_sync_get_metrics, scope, channel.value, query_items)

        # format human-readable output for the ai
        lines = [f"--- ch{channel.value} measurements ---"]
        for k, v in res.items():
            if v is None:
                val_display = "n/a (no stable signal)"
            elif k == "FREQ":
                val_display = f"{v:.2f} hz" if v < 1000 else f"{v/1000:.4f} khz"
            else:
                val_display = f"{v:.4f} v"
            lines.append(f"{k}: {val_display}")

        return "\n".join(lines)

    @mcp.tool()
    async def clear_measurements() -> str:
        """
        clears all active measurement boxes from the display.
        use this to reset the visual layout before a new calibration step.
        """
        return await asyncio.to_thread(_sync_clear_measurements, scope)
