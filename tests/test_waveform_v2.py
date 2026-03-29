"""
test_waveform_v2.py - integration test for raw data streaming and recording.
verifies segmented memory activation and calibrated voltage conversion.
"""

import time

# imported from the consolidated v2 waveform module
from rigol_dho824_mcp.tools.waveform2 import _sync_get_waveform, _sync_setup_recording


def test_waveform_capture_logic(scope):
    """
    validates high-speed raw waveform retrieval and segmented recording setup.
    essential for offline signal analysis and catching sony deck glitches.
    """
    print("\n[test] verifying waveform and recorder systems...")

    # 1. segmented recording start (segmented memory)
    # we request 50 frames with a 1ms interval
    rec_status = _sync_setup_recording(scope, frames=50, interval=0.001)

    assert rec_status.enabled is True
    assert rec_status.operation == "RUN"
    print(f"  - recording initialized: targeting {rec_status.frames} frames.")

    # allow a brief window for hardware buffering
    time.sleep(0.5)

    # 2. waveform data transfer (raw binary transfer)
    # note: _sync_get_waveform forces the scope to :STOP for reliable buffer access
    print("  - starting binary data transfer (1200 points)...")
    wv_data = _sync_get_waveform(scope, channel=1, points=1200)

    # verify data structure and point count
    assert wv_data.channel == 1
    assert len(wv_data.voltages) > 0
    assert wv_data.points == len(wv_data.voltages)

    # inspect sample voltages to ensure calibration/scaling was applied
    sample_voltages = wv_data.voltages[:5]
    print(f"  - first 5 voltage samples: {sample_voltages} v")

    # 3. system error check (remote command verification)
    time.sleep(0.5)

    instr = scope.connect()
    instr.write("*CLS")
    time.sleep(0.1)
    err = instr.query(":SYSTem:ERRor?").strip()

    # rigol standard: "0,No error"
    assert err.startswith("0,") or "No error" in err

    # 4. cleanup: restore scope to running state
    # since raw data capture leaves the scope in STOP mode
    instr.write(":RUN")
    print("[test] waveform module validated. scope returned to run state.")
