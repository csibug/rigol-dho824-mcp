"""
common2.py - shared constants, enums, and utility functions for rigol dho824.
part of the tape deck calibration toolkit.
"""

import asyncio
import os
from enum import Enum
from typing import Annotated, Optional, TypedDict

from pydantic import BaseModel, Field

# --- enums (configuration and state) ---

class ChannelNumber(int, Enum):
    CH1 = 1
    CH2 = 2
    CH3 = 3
    CH4 = 4

class AcquisitionType(str, Enum):
    NORMAL = "NORM"
    AVERAGE = "AVER"
    PEAK = "PEAK"
    HIGH_RES = "HRES"

class MemoryDepth(str, Enum):
    AUTO = "AUTO"
    K1 = "1K"
    K10 = "10K"
    K100 = "100K"
    M1 = "1M"
    M10 = "10M"
    M25 = "25M"
    M50 = "50M"

class TriggerSlope(str, Enum):
    POSITIVE = "POSitive"
    NEGATIVE = "NEGative"
    EITHER = "EITHer"

class TriggerSweep(str, Enum):
    """trigger sweep modes (auto, normal, single)."""
    AUTO = "AUTO"
    NORMAL = "NORMal"
    SINGLE = "SINGle"

class TriggerType(str, Enum):
    """trigger event types."""
    EDGE = "EDGE"
    PULSE = "PULSe"
    TIMEOUT = "TIMeout"

class SystemAction(str, Enum):
    """standard system-level operations."""
    RESET = "RESET"
    CLEAR_DISPLAY = "CLEAR_DISPLAY"
    FORCE_TRIGGER = "FORCE_TRIGGER"
    SCREENSHOT = "SCREENSHOT"

# --- data models (pydantic / typeddict) ---

class ActionResult(BaseModel):
    """standard response for successful hardware operations."""
    action: SystemAction
    status: str = "success"
    message: Optional[str] = None

class ScreenshotResult(TypedDict):
    """result model for screen capture operations."""
    file_path: Annotated[str, Field(description="local path to the saved png")]
    image_base64: Annotated[Optional[str], Field(default=None, description="base64 encoded image for ai vision")]

# --- mapping functions (response interpretation) ---

def map_trigger_sweep(raw_sweep: str) -> str:
    """translates raw :TRIG:SWE? responses to human-readable format."""
    mapping = {
        "AUTO": "Auto",
        "NORM": "Normal",
        "SING": "Single"
    }
    return mapping.get(raw_sweep.strip().upper(), f"Unknown ({raw_sweep})")

def map_trigger_status(raw_status: str) -> str:
    """translates raw :TRIG:STAT? responses (TD, WAIT, STOP, etc.)."""
    mapping = {
        "TD": "Triggered",
        "WAIT": "Wait",
        "RUN": "Run",
        "STOP": "Stop",
        "AUTO": "Auto"
    }
    return mapping.get(raw_status.strip().upper(), f"Unknown ({raw_status})")

# --- shared helper functions ---

async def capture_screenshot_shared(scope, prefix: str, directory: str = "data/screenshots") -> str:
    """
    shared logic for capturing and saving a png screenshot.
    saves files to the specified directory (defaulting to data/screenshots).
    """
    # biztosítjuk a mappa létezését (most már a megadott helyen)
    os.makedirs(directory, exist_ok=True)

    filename = f"{prefix}.png"
    filepath = os.path.join(directory, filename)

    def _sync_capture():
        instr = scope.connect()
        # dho824 returns raw binary png data
        # full command is :DISPlay:DATA?
        raw_data = instr.query_binary_values(":DISPlay:DATA? PNG", datatype='B', container=bytes)
        with open(filepath, "wb") as f:
            f.write(raw_data)
        return filepath

    return await asyncio.to_thread(_sync_capture)
