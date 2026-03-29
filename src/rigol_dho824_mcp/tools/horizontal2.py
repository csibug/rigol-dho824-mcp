"""
horizontal2.py - timebase and horizontal system configuration.
essential for tape deck speed (wow/flutter) and phase (azimuth) analysis.
"""

import asyncio
from enum import Enum
from typing import Optional

from typing_extensions import NotRequired, TypedDict

# === ENUMS & SCHEMAS ===

class HorizontalScale(str, Enum):
    """
    inspector-friendly names with raw scpi values.
    optimized for audio frequency analysis on the rigol dho824.
    """
    S1      = "1.0"
    MS_500  = "0.5"
    MS_200  = "0.2"
    MS_100  = "0.1"
    MS_50   = "0.05"
    MS_20   = "0.02"
    MS_10   = "0.01"
    MS_5    = "0.005"
    MS_2    = "0.002"
    MS_1    = "0.001"    # recommended for 3000 hz speed checks
    US_500  = "0.0005"
    US_200  = "0.0002"
    US_100  = "0.0001"   # standard for 10 khz signals
    US_50   = "0.00005"  # 10 khz (approx. 5 cycles)
    US_20   = "0.00002"  # 10 khz (approx. 2 cycles - BEST FOR AZIMUTH)
    US_10   = "0.00001"

class TimebaseState(TypedDict):
    """current horizontal configuration of the oscilloscope."""
    mode: str
    scale: float
    offset: float
    zoom_enabled: bool
    zoom_scale: NotRequired[float]

# === LOGIC (synchronous hardware interaction) ===

def _sync_get_timebase_state(scope) -> TimebaseState:
    """reads the full horizontal configuration (scale, offset, zoom)."""
    instr = scope.connect()

    # fetch core timebase values
    mode = instr.query(":TIMebase:MODE?").strip()
    scale = float(instr.query(":TIMebase:SCALe?"))
    offset = float(instr.query(":TIMebase:OFFSet?"))
    zoom_on = instr.query(":TIMebase:DELay:ENABle?").strip() in ("1", "ON")

    state: TimebaseState = {
        "mode": mode,
        "scale": scale,
        "offset": offset,
        "zoom_enabled": zoom_on
    }

    if zoom_on:
        # fetch secondary zoom scale if enabled
        state["zoom_scale"] = float(instr.query(":TIMebase:DELay:SCALe?"))

    return state

def _sync_set_timebase(
    scope,
    scale: Optional[str] = None,
    offset: Optional[float] = None,
    zoom: Optional[bool] = None
) -> TimebaseState:
    """sets horizontal parameters and returns the updated state."""
    instr = scope.connect()

    if scale is not None:
        instr.write(f":TIMebase:SCALe {scale}")

    if offset is not None:
        instr.write(f":TIMebase:OFFSet {offset}")

    if zoom is not None:
        status = "ON" if zoom else "OFF"
        instr.write(f":TIMebase:DELay:ENABle {status}")

    return _sync_get_timebase_state(scope)

# === MCP TOOLS ===

def register_horizontal_tools(mcp, scope):
    """registers horizontal/timebase tools with the mcp server."""

    @mcp.tool()
    async def get_timebase() -> TimebaseState:
        """returns current timebase settings (scale, offset, and zoom state)."""
        return await asyncio.to_thread(_sync_get_timebase_state, scope)

    @mcp.tool()
    async def set_timebase(
        scale: Optional[HorizontalScale] = None,
        offset: float = 0.0,
        zoom_enabled: Optional[bool] = None
    ) -> TimebaseState:
        """
        configures the oscilloscope timebase.
        - use MS_1 for 3khz speed/wow measurement.
        - use US_20 for 10khz azimuth alignment.
        """
        scale_val = scale.value if scale else None
        return await asyncio.to_thread(
            _sync_set_timebase, scope, scale_val, offset, zoom_enabled
        )

    @mcp.tool()
    async def set_zoom_scale(scale: HorizontalScale) -> str:
        """configures the magnified zoom window scale (requires zoom_enabled=true)."""
        def _zoom():
            instr = scope.connect()
            instr.write(f":TIMebase:DELay:SCALe {scale.value}")
            return f"zoom scale updated: {scale.value} s/div"

        return await asyncio.to_thread(_zoom)
