"""
waveform2.py - advanced waveform capture and segmented recording tools.
enables raw data export and glitch capture for sony tape deck analysis.
"""

import asyncio
import time
from enum import Enum
from typing import List

from pydantic import BaseModel

from .common2 import ChannelNumber

# === TYPES ===

class RecordingOperation(str, Enum):
    """standard recording states."""
    RUN = "RUN"
    STOP = "STOP"

class WaveformRecordingResult(BaseModel):
    """summary of a segmented recording session."""
    enabled: bool
    operation: str
    frames: int
    max_frames: int

class WaveformSeries(BaseModel):
    """raw voltage data series for high-precision analysis."""
    channel: int
    points: int
    voltages: List[float]

# === LOGIC (synchronous hardware interaction) ===

def _sync_setup_recording(scope, frames: int, interval: float) -> WaveformRecordingResult:
    """configures and starts a segmented waveform recording."""
    instr = scope.connect()

    # enable recording and wait for gui to initialize
    instr.write(":RECord:WRECord:ENABle ON")
    time.sleep(0.5)

    instr.write(f":RECord:WRECord:FRAMes {frames}")
    instr.write(f":RECord:WRECord:FINTerval {interval}")
    instr.write(":RECord:WRECord:OPERate RUN")

    # brief pause to confirm start
    time.sleep(0.2)

    return WaveformRecordingResult(
        enabled=True,
        operation="RUN",
        frames=int(instr.query(":RECord:WRECord:FRAMes?")),
        max_frames=int(instr.query(":RECord:WRECord:FMAX?"))
    )

def _sync_get_waveform(scope, channel: int, points: int = 1000) -> WaveformSeries:
    """captures waveform data with calibrated voltage scaling for dho800 series."""
    instr = scope.connect()

    # scope must be in stop mode for reliable raw data buffer access
    instr.write(":STOP")
    time.sleep(0.1)

    instr.write(f":WAVeform:SOURce CHANnel{channel}")
    instr.write(":WAVeform:MODE NORMal")
    instr.write(":WAVeform:FORMat BYTE")
    instr.write(f":WAVeform:POINts {points}")

    # fetch preamble data for scaling conversion
    # format: type, mode, points, count, x_inc, x_orig, x_ref, y_inc, y_orig, y_ref
    pre = instr.query(":WAVeform:PREamble?").split(",")
    y_inc = float(pre[7])
    y_orig = float(pre[8])
    y_ref = float(pre[9])

    # binary data transfer
    raw_data = instr.query_binary_values(":WAVeform:DATA?", datatype='B', container=list)

    # dho conversion formula: voltage = (raw_byte - y_origin - y_reference) * y_increment
    voltages = [(float(val) - y_orig - y_ref) * y_inc for val in raw_data]

    return WaveformSeries(
        channel=channel,
        points=len(voltages),
        voltages=voltages
    )

# === MCP TOOLS ===

def register_waveform_tools(mcp, scope):
    """registers waveform capture and recording tools with the mcp server."""

    @mcp.tool()
    async def capture_recording(frames: int = 100, interval: float = 0.001) -> WaveformRecordingResult:
        """
        starts a segmented waveform recording.
        ideal for catching transient glitches or intermittent dropouts on the sony deck.
        """
        return await asyncio.to_thread(_sync_setup_recording, scope, frames, interval)

    @mcp.tool()
    async def get_waveform_data(
        channel: ChannelNumber = ChannelNumber.CH1,
        points: int = 1200
    ) -> WaveformSeries:
        """
        downloads raw voltage data points from the scope's screen buffer.
        useful for detailed external signal analysis or software-based wow/flutter checks.
        """
        return await asyncio.to_thread(_sync_get_waveform, scope, channel.value, points)
