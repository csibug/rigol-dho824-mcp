"""
test_system_v2.py - integration test for visual and utility tools.
verifies screenshot capture integrity and display clearing logic.
"""

import os

import pytest

# imported from the consolidated v2 system module (formerly utility2)
from rigol_dho824_mcp.tools.utility2 import clear_display_logic, get_screenshot_logic


@pytest.mark.asyncio
async def test_system_visual_tools(scope):
    """
    validates screenshot capture and display clearing functionality.
    ensures the ai can 'see' the sony deck's signals via base64 images.
    """
    print("\n[test] verifying system/visual utility tools...")

    # 1. capture screenshot (essential for ai vision analysis)
    shot = await get_screenshot_logic(scope)

    # verify file exists on disk
    assert shot["file_path"] is not None
    assert os.path.exists(shot["file_path"])

    # verify base64 encoding (must be present and have significant size)
    b64_data = shot["image_base64"]
    assert b64_data is not None, "screenshot base64 data is missing!"
    assert len(b64_data) > 1000

    print(f"  - screenshot successful: {shot['file_path']} (size: {len(b64_data)} chars)")

    # 2. clear display (cleans waveforms and measurement boxes)
    result = await clear_display_logic(scope)

    # check if the action constant matches our systemaction enum
    assert "CLEAR_DISPLAY" in str(result.action)
    print("  - display clear successful.")

    # 3. system error check (remote command verification)
    instr = scope.connect()
    err = instr.query(":SYSTem:ERRor?").strip()

    # rigol standard: "0,No error" or similar starting with "0,"
    assert err.startswith("0,") or "No error" in err

    print("[test] system visual module fully validated.")
