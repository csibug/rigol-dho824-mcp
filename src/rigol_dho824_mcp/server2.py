"""
server2.py - the main entry point for the rigol dho824 mcp v2 server.
consolidates all modular tools into a single fastmcp instance.
"""

import asyncio
import os
import time
from typing import Optional, cast

import pyvisa
from dotenv import load_dotenv
from fastmcp import FastMCP
from pyvisa.resources import MessageBasedResource

# module registrations
from .tools.acquire2 import register_acquire_tools
from .tools.channel2 import register_channel_tools  # fixed name to match our 'channels2.py'
from .tools.decode2 import register_decode_tools
from .tools.horizontal2 import register_horizontal_tools
from .tools.measure2 import register_measure_tools
from .tools.multimeter2 import register_multimeter_tools
from .tools.trigger2 import register_trigger_tools
from .tools.utility2 import register_system_tools  # fixed name to match our 'system2.py'
from .tools.waveform2 import register_waveform_tools

# configuration
INTERNAL_DIR = os.path.dirname(os.path.abspath(__file__))

# visszalépünk kettőt a gyökérbe: .../rigol-dho824-mcp/
ROOT_DIR = os.path.dirname(os.path.dirname(INTERNAL_DIR))

# központi adatgyűjtő
DATA_DIR = os.path.join(ROOT_DIR, "data")
# ide kerülnek a screenshotok (png)
SCREENSHOTS_DIR = os.path.join(DATA_DIR, "screenshots")
# ide kerülnek a hullámformák (csv, bin)
WAVEFORMS_DIR = os.path.join(DATA_DIR, "waveforms")

# könyvtárak létrehozása
for d in [DATA_DIR, SCREENSHOTS_DIR, WAVEFORMS_DIR]:
    os.makedirs(d, exist_ok=True)


load_dotenv()
resource_env = os.getenv("RIGOL_RESOURCE")
if resource_env is None:
    raise ValueError("RIGOL_RESOURCE not found in environment variables. check your .env file.")

RIGOL_RESOURCE: str = resource_env
VISA_TIMEOUT = int(os.getenv("VISA_TIMEOUT", "30000"))

# initialize fastmcp
mcp = FastMCP("rigol-dho824-v2")

class RigolDHO824:
    """manages the persistent visa connection to the hardware."""
    def __init__(self, resource_string: str, timeout: int = 10000):
        self.rm = pyvisa.ResourceManager('@py')
        self.resource_string = resource_string
        self.timeout = timeout
        self.instr: Optional[MessageBasedResource] = None

    def connect(self) -> MessageBasedResource:
        """establishes a persistent connection if not already active."""
        if self.instr is None:
            raw = self.rm.open_resource(self.resource_string)
            self.instr = cast(MessageBasedResource, raw)
            self.instr.timeout = self.timeout
            self.instr.write_termination = "\n"
            self.instr.read_termination = "\n"
        return self.instr

    def close(self):
        """closes the instrument connection and releases resources."""
        if self.instr is not None:
            try:
                self.instr.close()
            except Exception:
                pass
            finally:
                self.instr = None

# initialize the global scope instance
scope = RigolDHO824(RIGOL_RESOURCE, VISA_TIMEOUT)

# --- system-level tools ---

@mcp.tool()
async def hello_rigol() -> str:
    """simple connectivity test to verify hardware communication."""
    def _sync_work():
        instr = scope.connect()
        idn = instr.query("*IDN?").strip()
        return f"connection successful! hardware identity: {idn}"

    return await asyncio.to_thread(_sync_work)

@mcp.tool()
async def reset_scope() -> str:
    """fully resets the scope to factory defaults (*RST)."""
    def _work():
        instr = scope.connect()
        instr.write("*RST")
        time.sleep(2) # grace period for internal reboot
        return "scope reset to factory defaults completed."

    return await asyncio.to_thread(_work)

@mcp.tool()
async def trigger_autoset() -> str:
    """
    executes automated signal capture (autoset).
    ensures autoscale functionality is enabled before execution.
    """
    def _work():
        instr = scope.connect()
        instr.write(":SYSTem:AUToscale ON")
        time.sleep(0.05)
        instr.write(":AUToset")
        time.sleep(4) # allow time for hardware ranging
        return "autoset finished. hardware adjusted for current signals."

    return await asyncio.to_thread(_work)

# --- registration of modular tools ---

register_trigger_tools(mcp, scope)
register_acquire_tools(mcp, scope, temp_dir=WAVEFORMS_DIR)
register_measure_tools(mcp, scope)
register_horizontal_tools(mcp, scope)
register_channel_tools(mcp, scope)
register_decode_tools(mcp, scope)
register_multimeter_tools(mcp, scope)
register_waveform_tools(mcp, scope)
register_system_tools(mcp, scope)

if __name__ == "__main__":
    # check captures directory exists once more before running
    if not os.path.exists(WAVEFORMS_DIR):
        os.makedirs(WAVEFORMS_DIR)

    mcp.run()
