"""
test_channel_v2.py - integration test for vertical channel configuration.
verifies sony-specific deck calibration settings (ac coupling, 20m bwl).
"""

from rigol_dho824_mcp.tools.channel2 import ChannelCoupling, _sync_set_channel


def test_channel_sony_logic(scope):
    """
    verifies channel leveling, 20m bandwidth limit, and custom labeling.
    simulates the standard setup for sony tc-fx44 audio analysis.
    """
    print("\n[test] verifying vertical channel system...")

    # 1. simulate sony deck calibration setup: ch1, ac, 500mv, 20mhz filter, label
    res = _sync_set_channel(
        scope,
        channel=1,
        enabled=True,
        coupling=ChannelCoupling.AC,
        scale=0.5,
        bw_20M=True,
        label="SONY_L"
    )

    # 2. verify based on the returned state dictionary
    # the dho800 returns 'AC' for coupling and '20M' for bwl
    assert res["coupling"] == "AC"
    assert res["scale"] == 0.5
    assert res["bw_limit"] == "20M"
    assert res["label"] == "SONY_L"

    # 3. cleanup: reset to neutral state to avoid leaving labels on screen
    _sync_set_channel(scope, channel=1, bw_20M=False, label="CH1")

    # 4. system error check: ensure no scpi errors were generated during config
    instr = scope.connect()
    err = instr.query(":SYSTem:ERRor?").strip()

    # rigol standard: "0,No error" or similar starting with "0,"
    assert err.startswith("0,") or "No error" in err

    print(f"[test] channel vertical system ok. result: {res['coupling']}, {res['bw_limit']}")
