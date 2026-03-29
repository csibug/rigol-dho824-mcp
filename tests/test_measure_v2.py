"""
test_measure_v2.py - integration test for automatic measurements.
verifies metric retrieval (vpp, freq) and display cleanup functionality.
"""

import time

# imported from the consolidated v2 measure module
from rigol_dho824_mcp.tools.measure2 import MeasureItem, _sync_clear_measurements, _sync_get_metrics


def test_measurement_and_clear(scope):
    """
    verifies that measurements can be activated, retrieved, and cleared
    without generating scpi system errors.
    """
    instr = scope.connect()

    # 1. preparation: clear existing measurements for a clean start
    instr.write(":MEASure:CLEar")
    time.sleep(0.5)

    # 2. execution: fetch vpp and frequency
    # _sync_get_metrics handles activation on the scope display automatically
    results = _sync_get_metrics(
        scope,
        channel=1,
        items=[MeasureItem.VPP, MeasureItem.FREQ]
    )

    # verify dictionary keys exist (values might be None if no signal is present)
    assert "VPP" in results
    assert "FREQ" in results

    print(f"[test] retrieved metrics: vpp={results['VPP']}, freq={results['FREQ']}")

    # 3. execution: clear display via the dedicated tool
    status_after = _sync_clear_measurements(scope)

    # 4. final system check: ensure no errors remain in the buffer
    # we reconnect to ensure we have the latest instruction handle
    instr = scope.connect()
    final_error = instr.query(":SYSTem:ERRor?").strip()

    # rigol standard: "0,No error"
    assert final_error.startswith("0,") or "No error" in final_error

    print(f"\n[test] measurement tool status: {status_after}")
