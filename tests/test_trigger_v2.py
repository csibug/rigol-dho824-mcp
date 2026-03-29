"""
test_trigger_v2.py - integration test for trigger logic.
ensures hardware communication and response formatting are correct.
"""

import asyncio

import pytest

# use the consolidated server2 scope
from rigol_dho824_mcp.server2 import scope

# use the new common2 for enums
from rigol_dho824_mcp.tools.common2 import TriggerSlope

# import the direct logic for testing
from rigol_dho824_mcp.tools.trigger2 import set_edge_trigger_logic


@pytest.mark.asyncio
async def test_trigger_v2_integration():
    """
    tests the edge trigger logic directly on the hardware.
    verifies that the return string matches the new lowercase v2 standard.
    """
    try:
        print("\n[test] setting edge trigger directly...")

        # testing with specific values for a sony deck calibration scenario
        result = await set_edge_trigger_logic(
            scope,
            channel=1,
            level=1.2,
            slope=TriggerSlope.NEGATIVE,
            sweep="NORMal",
            coupling="LFReject"
        )

        # lowercase check to match v2 tools/trigger2.py output
        assert "edge trigger verified" in result
        assert "ch1" in result
        assert "1.2v" in result
        assert "NORMal" in result

        print(f"[test] hardware response: {result}")

    finally:
        print("[test] cleaning up hardware state...")
        # restore scope to a safe, neutral auto-trigger state
        await set_edge_trigger_logic(
            scope,
            channel=1,
            level=1.5,
            slope=TriggerSlope.POSITIVE,
            sweep="AUTO",
            coupling="DC"
        )

if __name__ == "__main__":
    # allow manual execution of the test script
    asyncio.run(test_trigger_v2_integration())
