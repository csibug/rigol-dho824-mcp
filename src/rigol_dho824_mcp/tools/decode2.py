"""
decode2.py - protocol decoding tools (uart/rs232).
part of the rigol dho824 mcp project for logic and bus analysis.
"""

import asyncio
import time
from enum import Enum

from typing_extensions import TypedDict

from .common2 import ChannelNumber

# === ENUMS & TYPES ===

class BusFormat(str, Enum):
    HEX = "HEX"
    DEC = "DEC"
    BIN = "BIN"
    ASCII = "ASCii"

class DecodeConfigResult(TypedDict):
    """summary of the current protocol decoder status."""
    bus: int
    mode: str
    enabled: bool
    format: str

# === LOGIC (synchronous hardware interaction) ===

def _sync_get_decode_status(scope, bus: int) -> DecodeConfigResult:
    """reads the current status and display format of a specific bus."""
    instr = scope.connect()

    mode = instr.query(f":BUS{bus}:MODE?").strip()
    enabled = instr.query(f":BUS{bus}:DISP?") == "1"
    fmt = instr.query(f":BUS{bus}:FORM?").strip()

    return {
        "bus": bus,
        "mode": mode,
        "enabled": enabled,
        "format": fmt
    }

def _sync_set_uart_decode(
    scope,
    bus: int,
    rx_chan: int,
    baud: int,
    enabled: bool = True
) -> DecodeConfigResult:
    """
    configures a basic uart (rs232) decoder for logic debugging.
    defaults to 8n1, lsb first as per standard protocols.
    """
    instr = scope.connect()

    # set fundamental rs232 parameters
    instr.write(f":BUS{bus}:MODE RS232")
    instr.write(f":BUS{bus}:RS232:RX CHAN{rx_chan}")
    instr.write(f":BUS{bus}:RS232:BAUD {baud}")
    instr.write(f":BUS{bus}:RS232:DBIT 8")
    instr.write(f":BUS{bus}:RS232:PAR NONE")
    instr.write(f":BUS{bus}:RS232:SBIT 1")
    instr.write(f":BUS{bus}:DISP {'ON' if enabled else 'OFF'}")

    # allow hardware to initialize the decoder ribbon
    time.sleep(0.05)
    return _sync_get_decode_status(scope, bus)

def _sync_read_bus_data(scope, bus: int) -> str:
    """fetches the string of characters currently in the screen's decode buffer."""
    instr = scope.connect()
    # returns raw text data from the specified bus
    return instr.query(f":BUS{bus}:DATA?").strip()

# === MCP TOOLS ===

def register_decode_tools(mcp, scope):
    """registers bus decoding tools with the mcp server."""

    @mcp.tool()
    async def setup_uart_decode(
        bus: int = 1,
        rx_channel: ChannelNumber = ChannelNumber.CH4,
        baud_rate: int = 9600
    ) -> DecodeConfigResult:
        """
        quickly configures uart decoding on a specific channel.
        useful for debugging digital control signals in tape decks.
        """
        return await asyncio.to_thread(
            _sync_set_uart_decode, scope, bus, rx_channel.value, baud_rate
        )

    @mcp.tool()
    async def get_decoded_text(bus: int = 1) -> str:
        """reads the currently decoded text directly from the scope's bus buffer."""
        return await asyncio.to_thread(_sync_read_bus_data, scope, bus)

    @mcp.tool()
    async def set_bus_format(
        bus: int = 1,
        format: BusFormat = BusFormat.ASCII
    ) -> DecodeConfigResult:
        """sets the visual format for decoded data (e.g., hex, ascii, binary)."""
        def _work():
            instr = scope.connect()
            instr.write(f":BUS{bus}:FORM {format.value}")
            return _sync_get_decode_status(scope, bus)

        return await asyncio.to_thread(_work)
