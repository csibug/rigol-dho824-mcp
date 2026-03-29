import os
import shutil
import tempfile

import pytest

from rigol_dho824_mcp.server2 import RigolDHO824  # Feltételezve, hogy itt van a Scope osztályod


@pytest.fixture(scope="session")
def scope():
    resource = os.getenv("RIGOL_RESOURCE", "TCPIP0::127.0.0.1::inst0::INSTR")
    timeout = int(os.getenv("VISA_TIMEOUT", "5000"))
    s = RigolDHO824(resource, timeout)
    yield s
    s.close()

@pytest.fixture
def temp_dir():
    """Létrehoz egy ideiglenes mappát a mentéseknek, majd a teszt után törli."""
    path = tempfile.mkdtemp(prefix="pytest_rigol_")
    yield path
    shutil.rmtree(path)
