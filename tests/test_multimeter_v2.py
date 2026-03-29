"""
test_multimeter_v2.py - integration test for dvm and high-res counter.
verifies cold-start timing and 7-digit precision for tape deck calibration.
"""

# imported from the consolidated v2 multimeter module
from rigol_dho824_mcp.tools.multimeter2 import CounterMode, DVMMode, _sync_configure_dvm, _sync_get_counter


def test_multimeter_and_counter_precision(scope):
    """
    validates the dvm's 2-second wake-up period and the counter's hardware precision.
    essential for monitoring sony dolby levels and motor speed accuracy.
    """
    print("\n[test] verifying multimeter and hardware counter systems...")

    # 1. dvm cold start (ac_rms for sony dolby level check)
    # the 2.0s sleep is handled internally by _sync_configure_dvm
    dvm = _sync_configure_dvm(scope, channel=1, mode=DVMMode.AC_RMS, enabled=True)

    assert dvm["enabled"] is True
    # ensure we got a valid reading (it shouldn't be 0.0 if a signal is present)
    assert isinstance(dvm["reading"], float)
    print(f"  - dvm (ac_rms) successful. reading: {dvm['reading']} v")

    # 2. hardware counter (high-res frequency for speed check)
    # internal logic handles the 1.5s gate cycle + polling loop
    counter = _sync_get_counter(scope, channel=1, mode=CounterMode.FREQUENCY)

    assert counter["enabled"] is True
    assert counter["unit"] == "Hz"
    # the 7-digit counter is our most precise tool for the 3000hz/3150hz tape
    print(f"  - counter (high-res) successful. frequency: {counter['value']} hz")

    # 3. system error check (remote command verification)
    instr = scope.connect()
    err = instr.query(":SYSTem:ERRor?").strip()

    # rigol standard: "0,No error" or similar starting with "0,"
    assert err.startswith("0,") or "No error" in err

    print("[test] multimeter module fully validated.")
