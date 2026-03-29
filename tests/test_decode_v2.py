"""
test_decode_v2.py - integration test for protocol decoding (uart/rs232).
verifies bus configuration and data retrieval from the scope's buffer.
"""

import time

# imported from the consolidated v2 decode module
from rigol_dho824_mcp.tools.decode2 import _sync_read_bus_data, _sync_set_uart_decode


def test_uart_decode_and_read(scope):
    """
    verifies uart decoder initialization and data reading capabilities.
    ensures the decoder ribbon can be enabled and disabled cleanly.
    """
    print("\n[test] verifying protocol decode system...")

    # 1. configure uart bus (ch4, 115200 baud)
    # this displays the decoder ribbon at the bottom of the scope screen
    status = _sync_set_uart_decode(
        scope,
        bus=1,
        rx_chan=4,
        baud=115200,
        enabled=True
    )

    assert status["enabled"] is True
    assert "RS232" in status["mode"]

    # allow a brief moment for the hardware bus to initialize
    time.sleep(0.5)

    # 2. data retrieval (ascii format)
    # even with no active traffic, the response must be a valid string (empty or null)
    data = _sync_read_bus_data(scope, bus=1)
    assert isinstance(data, str)
    print(f"  - bus 1 data read successful: '{data}'")

    # 3. cleanup: disable decoder
    # essential to remove visual clutter during sensitive sony deck measurements
    status_off = _sync_set_uart_decode(
        scope,
        bus=1,
        rx_chan=4,
        baud=115200,
        enabled=False
    )
    assert status_off["enabled"] is False

    # 4. system error check
    # ensures no invalid scpi commands were sent during the process
    instr = scope.connect()
    err = instr.query(":SYSTem:ERRor?").strip()

    # rigol standard: "0,No error" or similar starting with "0,"
    assert err.startswith("0,") or "No error" in err

    print("[test] decode module validated. status: idle.")
