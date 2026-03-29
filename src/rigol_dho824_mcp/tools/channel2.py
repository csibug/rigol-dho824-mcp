"""
channels2.py - channel configuration and state management.
part of the rigol dho824 mcp project.
"""

import asyncio
import time
from enum import Enum
from typing import Optional, cast

from typing_extensions import TypedDict

from .common2 import ChannelNumber

# === ENUMS & TYPES ===

class ChannelCoupling(str, Enum):
    AC = "AC"
    DC = "DC"
    GND = "GND"

class ChannelConfigResult(TypedDict):
    """detailed status of an oscilloscope channel."""
    channel: int
    enabled: bool
    coupling: str
    scale: float
    offset: float
    bw_limit: str
    label: str

# === LOGIC (synchronous hardware interaction) ===

def _sync_get_channel_config(scope, channel: int) -> ChannelConfigResult:
    """reads the current state of a specific channel."""
    instr = scope.connect()

    def _q(cmd):
        res = instr.query(cmd).strip()
        # small delay to prevent command overlapping on dho800
        time.sleep(0.03)
        return res

    try:
        enabled = _q(f":CHAN{channel}:DISP?") == "1"
        coupling = _q(f":CHAN{channel}:COUP?")
        scale = float(_q(f":CHAN{channel}:SCAL?"))
        offset = float(_q(f":CHAN{channel}:OFFS?"))
        bw_limit = _q(f":CHAN{channel}:BWL?")

        try:
            # fetch label content and strip quotes
            label = _q(f":CHAN{channel}:LAB:CONT?").strip('"')
        except Exception:
            label = ""

        # clear any potential hardware error flags
        instr.query(":SYST:ERR?")

        result: ChannelConfigResult = {
            "channel": channel,
            "enabled": enabled,
            "coupling": coupling,
            "scale": scale,
            "offset": offset,
            "bw_limit": bw_limit,
            "label": label
        }
        return cast(ChannelConfigResult, result)
    except Exception as e:
        # clear status on error to prevent blocking subsequent commands
        instr.write("*CLS")
        raise e

def _sync_set_channel(
    scope,
    channel: int,
    enabled: Optional[bool] = None,
    coupling: Optional[ChannelCoupling] = None,
    scale: Optional[float] = None,
    offset: Optional[float] = None,
    bw_20M: Optional[bool] = None,
    label: Optional[str] = None
) -> ChannelConfigResult:
    """performs hardware-level channel configuration."""
    instr = scope.connect()

    if enabled is not None:
        instr.write(f":CHAN{channel}:DISP {'ON' if enabled else 'OFF'}")
    if coupling is not None:
        instr.write(f":CHAN{channel}:COUP {coupling.value}")
    if scale is not None:
        instr.write(f":CHAN{channel}:SCAL {scale}")
    if offset is not None:
        instr.write(f":CHAN{channel}:OFFS {offset}")
    if bw_20M is not None:
        val = "20M" if bw_20M else "OFF"
        instr.write(f":CHAN{channel}:BWL {val}")
    if label is not None:
        # sanitize label content: max 8 chars and no quotes
        safe_label = label[:8].replace('"', '')
        instr.write(f':CHAN{channel}:LAB:CONT "{safe_label}"')
        instr.write(f":CHAN{channel}:LAB:SHOW ON")

    return _sync_get_channel_config(scope, channel)

# === MCP TOOLS ===

def register_channel_tools(mcp, scope):
    """registers channel-related tools with the mcp server."""

    @mcp.tool()
    async def get_channel_config(
        channel: ChannelNumber = ChannelNumber.CH1
    ) -> ChannelConfigResult:
        """fetches configuration for a specific channel (1-4). default: ch1."""
        return await asyncio.to_thread(_sync_get_channel_config, scope, channel.value)

    @mcp.tool()
    async def set_channel_config(
        channel: ChannelNumber = ChannelNumber.CH1,
        enabled: Optional[bool] = None,
        coupling: Optional[ChannelCoupling] = None,
        scale: Optional[float] = None,
        offset: Optional[float] = None,
        bw_20M: Optional[bool] = None,
        label: Optional[str] = None
    ) -> ChannelConfigResult:
        """
        configures a channel. recommended for sony deck: ac coupling, bw_20M=true.
        """
        return await asyncio.to_thread(
            _sync_set_channel,
            scope,
            channel.value,
            enabled,
            coupling,
            scale,
            offset,
            bw_20M,
            label
        )
