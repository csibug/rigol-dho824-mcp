"""
test_acquire_v2.py - integration test for raw data capture.
verifies file integrity and post-capture hardware state.
"""

import os
import time

# imported directly from the new v2 module
from rigol_dho824_mcp.tools.acquire2 import _sync_capture_raw


def test_capture_consistency(scope, temp_dir):
    """
    verifies that raw capture works and the scope successfully
    returns to a running state afterward.
    """
    # 1. precondition: ensure scope is running
    instr = scope.connect()
    instr.write(":RUN")
    time.sleep(0.5)

    # 2. execute raw capture (1000 points, 16-bit word format inside)
    path, count = _sync_capture_raw(scope, channel=1, points=1000, temp_dir=temp_dir)

    # 3. verify file and data integrity
    assert count == 1000
    assert os.path.exists(path)
    assert os.path.getsize(path) > 0

    # 4. CRITICAL: verify return to RUN/TRIGGERED state
    # we poll for up to 1 second to avoid flakiness on the android-based dho800
    settled_status = "STOP"
    for _ in range(10):
        status = instr.query(":TRIGger:STATus?").strip()
        if status in ["RUN", "TD", "WAIT", "AUTO"]:
            settled_status = status
            break
        time.sleep(0.1)

    assert settled_status != "STOP", f"scope stuck in STOP after capture. last: {settled_status}"
    print(f"\n[test] raw capture ok, file: {path}, status: {settled_status}")
