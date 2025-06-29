"""Configuration for pytest."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, create_autospec

import pytest


class MockWinreg:
    """A mock for the winreg module."""

    def __init__(self):
        """Initialise the mock."""
        self.HKEY_CLASSES_ROOT = "HKEY_CLASSES_ROOT"
        self.HKEY_LOCAL_MACHINE = "HKEY_LOCAL_MACHINE"
        self.registry = {}

    def OpenKey(self, key, sub_key):
        """Mock OpenKey."""
        if (key, sub_key) in self.registry:
            mock_key = MagicMock()
            mock_key.__enter__.return_value = (key, sub_key)
            return mock_key
        raise FileNotFoundError

    def QueryValueEx(self, key_handle, value_name):
        """Mock QueryValueEx."""
        key, sub_key = key_handle
        values = self.registry.get((key, sub_key), {})
        if value_name in values:
            return values[value_name], 0
        raise FileNotFoundError

    def SetValue(self, key, sub_key, value_name, value):
        """Set a value in the mock registry for testing."""
        if (key, sub_key) not in self.registry:
            self.registry[(key, sub_key)] = {}
        self.registry[(key, sub_key)][value_name] = value

    def Clear(self):
        """Clear the mock registry."""
        self.registry.clear()


@pytest.fixture
def mock_winreg():
    """Fixture to provide a mock winreg module."""
    mock = MockWinreg()
    sys.modules["winreg"] = mock
    yield mock
    del sys.modules["winreg"]


@pytest.fixture(autouse=True)
def caplog_for_loguru(caplog):
    """Fixture to configure Loguru to propagate to caplog."""
    import logging

    from loguru import logger

    class PropagateHandler(logging.Handler):
        def emit(self, record):
            logging.getLogger(record.name).handle(record)

    logger.add(PropagateHandler(), format="{message}")
    yield caplog
