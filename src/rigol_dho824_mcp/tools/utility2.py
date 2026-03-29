"""
system2.py - visual management and display tools for rigol dho824.
includes screenshot capture and screen clearing functionality.
"""

import asyncio
import base64
import datetime
import os

from .common2 import ActionResult, ScreenshotResult, SystemAction, capture_screenshot_shared

# === CORE LOGIC ===

async def clear_display_logic(scope) -> ActionResult:
    """
    clears both waveforms and all active measurement boxes from the screen.
    ensures a clean visual slate for new calibration steps.
    """
    def _sync_work():
        instr = scope.connect()
        # clear waveforms from the grid
        instr.write(":CLEar")
        # remove all measurement result windows
        instr.write(":MEASure:CLEar")
        return "display and measurements cleared."

    await asyncio.to_thread(_sync_work)
    return ActionResult(
        action=SystemAction.CLEAR_DISPLAY,
        status="success",
        message="screen and measurement windows cleared."
    )

async def get_screenshot_logic(scope) -> ScreenshotResult:
    """
    captures the current screen, saves it as png, and encodes it
    to base64 for ai vision analysis.
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = f"sony_deck_{timestamp}"

    # use shared screenshot logic from common2.py
    file_path = await capture_screenshot_shared(scope, prefix)

    # encode to base64 for direct ai integration
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
    else:
        b64 = None

    return ScreenshotResult(file_path=file_path, image_base64=b64)

# === TOOL REGISTRATION ===

def register_system_tools(mcp, scope):
    """registers visual and system-level utility tools with the mcp server."""

    @mcp.tool()
    async def clear_display() -> ActionResult:
        """
        clears waveforms and all measurement boxes from the scope's screen.
        use this to reset the display before a new test sequence.
        """
        return await clear_display_logic(scope)

    @mcp.tool()
    async def get_screenshot() -> ScreenshotResult:
        """
        captures the current oscilloscope screen as a png and base64.
        essential for providing visual signal evidence to the ai.
        """
        return await get_screenshot_logic(scope)
