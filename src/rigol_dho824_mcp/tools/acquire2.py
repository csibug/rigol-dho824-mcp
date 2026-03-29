"""
acquire2.py - waveform acquisition and raw data capture tools.
part of the rigol dho824 mcp project for tape deck calibration.
"""

import asyncio
import json
import os
import time
from typing import Optional, Tuple

from .common2 import AcquisitionType, ChannelNumber, MemoryDepth, TriggerSweep, map_trigger_sweep

# --- logic (synchronous work handled in separate thread) ---

def _sync_capture_raw(scope, channel: int, points: int, temp_dir: str) -> Tuple[str, int]:
    """
    downloads raw waveform data in 16-bit WORD format.
    ensures proper mode transitions to avoid dho800 series state lockup.
    """
    instr = scope.connect()

    # save initial state to restore it later
    initial_status = instr.query(":TRIGger:STATus?").strip()

    # scope must be in STOP to configure and read RAW memory reliably
    if initial_status != "STOP":
        instr.write(":STOP")
        time.sleep(0.1) # hardware grace period

    try:
        # configuration for deep memory access
        instr.write(f":WAVeform:SOURce CHANnel{channel}")
        instr.write(":WAVeform:MODE RAW")
        instr.write(":WAVeform:FORMat WORD") # 16-bit for 12-bit adc precision
        instr.write(f":WAVeform:STOP {points}")

        # fetch metadata for scaling conversion
        meta = {
            "yinc": float(instr.query(":WAVeform:YINCrement?")),
            "yor": float(instr.query(":WAVeform:YORigin?")),
            "yref": float(instr.query(":WAVeform:YREFerence?")),
            "xinc": float(instr.query(":WAVeform:XINCrement?")),
            "srat": float(instr.query(":ACQuire:SRATe?")),
        }

        # binary transfer (unsigned short, little endian)
        raw_values = instr.query_binary_values(":WAVeform:DATA?", datatype="H", is_big_endian=False)

        # save to json for post-processing (wow/flutter analysis)
        file_name = f"cap_ch{channel}_{len(raw_values)}pts.json"
        file_path = os.path.join(temp_dir, file_name)

        with open(file_path, 'w') as f:
            json.dump({"meta": meta, "data": list(raw_values)}, f)

        return file_path, len(raw_values)

    finally:
        # CRITICAL FIX: reset waveform mode to NORMAL before sending :RUN.
        # the dho824 waveform engine often blocks :RUN if left in RAW mode.
        instr.write(":WAVeform:MODE NORMal")

        if initial_status != "STOP":
            instr.write(":RUN")
            # give the scope's internal state machine a moment to re-trigger
            time.sleep(0.1)

# --- mcp tool registration ---

def register_acquire_tools(mcp, scope, temp_dir):

    @mcp.tool()
    async def set_acquisition_config(
        mode: Optional[AcquisitionType] = None,
        depth: Optional[MemoryDepth] = None
    ) -> str:
        """configures sample acquisition mode and memory depth."""
        def _sync():
            instr = scope.connect()
            if mode:
                instr.write(f":ACQuire:TYPE {mode.value}")
            if depth:
                instr.write(f":ACQuire:MDEPth {depth.value}")
            return f"acquisition updated: mode={mode}, depth={depth}"

        return await asyncio.to_thread(_sync)

    @mcp.tool()
    async def quick_capture(channel: ChannelNumber = ChannelNumber.CH1, points: int = 1000) -> str:
        """captures raw waveform data to json file for analysis."""
        path, count = await asyncio.to_thread(_sync_capture_raw, scope, channel.value, points, temp_dir)
        return f"raw capture success: {count} points. file: {path}"

    @mcp.tool()
    async def set_run_state(sweep: TriggerSweep) -> str:
        """controls scope trigger sweep: auto, normal, or single."""
        def _sync():
            instr = scope.connect()
            instr.write(f":TRIGger:SWEep {sweep.value}")
            current = instr.query(":TRIGger:SWEep?").strip()
            return f"trigger sweep set to: {map_trigger_sweep(current)}"

        return await asyncio.to_thread(_sync)
