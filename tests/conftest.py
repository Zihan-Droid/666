import sys, types
from pathlib import Path
import pytest

@pytest.fixture
def mock_nxopen(monkeypatch):
    if "NXOpen" in sys.modules: del sys.modules["NXOpen"]
    fake = types.ModuleType("NXOpen")
    fake.Session = type("Session",(),{})
    monkeypatch.setitem(sys.modules, "NXOpen", fake)
    return fake

@pytest.fixture
def project_root():
    return Path(__file__).resolve().parent.parent
