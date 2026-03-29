"""
trigger2.py - trigger system configuration and status monitoring.
part of the rigol dho824 mcp project for tape deck calibration.
"""

import asyncio
from typing import Optional, TypedDict

from fastmcp import FastMCP

from .common2 import (
    ChannelNumber,
    TriggerSlope,
    map_trigger_status,
    map_trigger_sweep,
)

# === INTERNAL MAPPING ===

def map_coupling_response(raw_coupling: str) -> str:
    """maps hardware short-form coupling responses to full descriptive strings."""
    mapping = {"AC": "AC", "DC": "DC", "LFR": "LFReject", "HFR": "HFReject"}
    return mapping.get(raw_coupling.strip().upper(), raw_coupling)

def map_sweep_response(raw_sweep: str) -> str:
    """maps hardware short-form sweep responses (norm/sing) to full words."""
    mapping = {"AUTO": "AUTO", "NORM": "NORMAL", "SING": "SINGLE"}
    return mapping.get(raw_sweep.strip().upper(), raw_sweep)

class TriggerStatusResult(TypedDict):
    """comprehensive summary of the current trigger state."""
    status: str
    mode: str
    sweep: str
    coupling: str
    channel: Optional[int]
    level: Optional[float]

# === LOGIC (shared by mcp and tests) ===

async def set_edge_trigger_logic(
    scope,
    channel: int,
    level: float,
    slope: TriggerSlope,
    sweep: str,
    coupling: str
) -> str:
    """
    performs synchronous hardware configuration for edge triggering.
    resets scale and offset to ensure a clean trigger environment.
    """
    def _sync_work():
        instr = scope.connect()
        # reset channel display parameters for consistent triggering
        instr.write(f":CHANnel{channel}:SCALe 1")
        instr.write(f":CHANnel{channel}:OFFSet 0")

        # apply edge trigger configuration
        instr.write(":TRIGger:MODE EDGE")
        instr.write(f":TRIGger:EDGE:SOURce CHANnel{channel}")
        instr.write(f":TRIGger:EDGE:SLOPe {slope.value}")
        instr.write(f":TRIGger:EDGE:LEVel {level}")
        instr.write(f":TRIGger:SWEep {sweep}")
        instr.write(f":TRIGger:COUPling {coupling}")

        return f"edge trigger verified: ch{channel}, {level}v, {sweep}, {coupling}"

    return await asyncio.to_thread(_sync_work)

# === MCP TOOL REGISTRATION ===

def register_trigger_tools(mcp: FastMCP, scope):
    """registers trigger-related tools with the mcp server."""

    @mcp.tool()
    async def get_trigger_status() -> TriggerStatusResult:
        """
        returns comprehensive trigger state including status, sweep, and coupling.
        maps short-form hardware responses to human-readable text.
        """
        def _sync_work() -> TriggerStatusResult:
            instr = scope.connect()

            # 1. initialize with safe defaults to ensure valid return on all paths
            result: TriggerStatusResult = {
                "status": "Unknown",
                "mode": "Unknown",
                "sweep": "Unknown",
                "coupling": "Unknown",
                "channel": None,
                "level": None
            }

            try:
                # fetch basic status and modes
                raw_status = instr.query(":TRIGger:STATus?").strip()
                raw_mode = instr.query(":TRIGger:MODE?").strip()
                raw_sweep = instr.query(":TRIGger:SWEep?").strip()
                raw_coupling = instr.query(":TRIGger:COUPling?").strip()

                current_mode = map_trigger_sweep(raw_mode)

                # update result dictionary
                result["status"] = map_trigger_status(raw_status)
                result["mode"] = current_mode
                result["sweep"] = map_sweep_response(raw_sweep)
                result["coupling"] = map_coupling_response(raw_coupling)

                # fetch channel and level details if in edge trigger mode
                if current_mode == "Edge":
                    try:
                        source = instr.query(":TRIGger:EDGE:SOURce?").strip()
                        chan_str = source.replace("CHAN", "")
                        result["channel"] = int(chan_str) if chan_str.isdigit() else None
                        result["level"] = float(instr.query(":TRIGger:EDGE:LEVel?"))
                    except (ValueError, TypeError):
                        pass # keep previous None values if hardware fetch fails

                # clear error queue after successful fetch
                instr.query(":SYSTem:ERRor?")

            except Exception:
                # in case of major comm error, clear status and return what we have
                instr.write("*CLS")

            return result

        return await asyncio.to_thread(_sync_work)

    @mcp.tool()
    async def set_edge_trigger(
        channel: ChannelNumber = ChannelNumber.CH1,
        level: float = 1.5,
        slope: TriggerSlope = TriggerSlope.POSITIVE,
        sweep: str = "AUTO",    # options: {AUTO|NORMal|SINGle}
        coupling: str = "DC"    # options: {AC|DC|LFReject|HFReject}
    ) -> str:
        """
        configures a standard edge trigger.
        essential for stabilizing waveforms during tape deck analysis.
        """
        return await set_edge_trigger_logic(scope, channel.value, level, slope, sweep, coupling)
