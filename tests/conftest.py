"""Configuration for pytest."""

import logging
import sys
from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock

import pytest


class MockWinreg:
    """A mock for the winreg module."""

    def __init__(self) -> None:
        """Initialise the mock."""
        self.HKEY_CLASSES_ROOT = "HKEY_CLASSES_ROOT"
        self.HKEY_LOCAL_MACHINE = "HKEY_LOCAL_MACHINE"
        self.registry: dict[tuple[str, str], dict[str, Any]] = {}

    def OpenKey(self, key: str, sub_key: str) -> MagicMock:
        """Mock OpenKey."""
        if (key, sub_key) in self.registry:
            mock_key = MagicMock()
            mock_key.__enter__.return_value = (key, sub_key)
            return mock_key
        raise FileNotFoundError

    def QueryValueEx(self, key_handle: tuple[str, str], value_name: str) -> tuple[str, int]:
        """Mock QueryValueEx."""
        key, sub_key = key_handle
        values = self.registry.get((key, sub_key), {})
        if value_name in values:
            return values[value_name], 0
        raise FileNotFoundError

    def SetValue(self, key: str, sub_key: str, value_name: str, value: Any) -> None:
        """Set a value in the mock registry for testing."""
        if (key, sub_key) not in self.registry:
            self.registry[(key, sub_key)] = {}
        self.registry[(key, sub_key)][value_name] = value

    def Clear(self) -> None:
        """Clear the mock registry."""
        self.registry.clear()


@pytest.fixture
def mock_winreg():  # noqa: ANN201
    """Fixture to provide a mock winreg module."""
    mock = MockWinreg()
    sys.modules["winreg"] = mock
    yield mock
    del sys.modules["winreg"]


@pytest.fixture(autouse=True)
def caplog_for_loguru(caplog: pytest.LogCaptureFixture) -> Generator[pytest.LogCaptureFixture, None, None]:
    """Fixture to configure Loguru to propagate to caplog."""
    from loguru import logger

    class PropagateHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            logging.getLogger(record.name).handle(record)

    handler_id = logger.add(PropagateHandler(), format="{message}")
    yield caplog
    logger.remove(handler_id)
