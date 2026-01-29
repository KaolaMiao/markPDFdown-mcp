import sys
import os
from pathlib import Path

# Add src to pythonpath for tests
src_path = Path(__file__).parent.parent / "src"
core_path = Path(__file__).parent.parent.parent / "markpdfdown_core" / "src"

sys.path.append(str(src_path))
sys.path.append(str(core_path))

import pytest

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"
