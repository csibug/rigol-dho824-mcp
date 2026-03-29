"""
test_horizontal_v2.py - integration test for timebase and horizontal systems.
verifies time scales and zoom (delayed sweep) functionality for tape deck analysis.
"""

import time

# imported from the consolidated v2 horizontal module
from rigol_dho824_mcp.tools.horizontal2 import HorizontalScale, _sync_set_timebase


def test_horizontal_and_zoom(scope):
    """
    verifies horizontal timebase scaling and the delayed zoom function.
    essential for accurate wow/flutter and frequency measurements.
    """
    print("\n[test] verifying horizontal timebase system...")

    # 1. baseline: 1ms/div (standard for sony tape speed calibration)
    # we use the raw value from our horizontalscale enum
    state = _sync_set_timebase(scope, scale=HorizontalScale.MS_1.value)

    # ensure the hardware scale matches our target (float comparison)
    assert float(state["scale"]) == 0.001
    time.sleep(0.2)

    # 2. zoom (delayed sweep) test: enable and disable
    # enable the magnifying window on the scope
    state_zoom = _sync_set_timebase(scope, zoom=True)
    assert state_zoom["zoom_enabled"] is True
    time.sleep(0.2)

    # disable the magnifying window
    state_back = _sync_set_timebase(scope, zoom=False)
    assert state_back["zoom_enabled"] is False

    # 3. system error check
    # ensures no scpi command errors occurred during transitions
    instr = scope.connect()
    err = instr.query(":SYSTem:ERRor?").strip()

    # rigol standard: "0,No error"
    assert err.startswith("0,") or "No error" in err

    print(f"[test] horizontal system ok. current scale: {state['scale']} s/div")
