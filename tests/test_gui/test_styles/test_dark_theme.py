"""Tests for DarkTheme styling."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication

from PrevisLib.gui.styles.dark_theme import DarkTheme


class TestDarkTheme:
    """Test cases for DarkTheme class."""

    def test_color_constants(self) -> None:
        """Test that all color constants are defined."""
        assert DarkTheme.BACKGROUND == "#1e1e1e"
        assert DarkTheme.SURFACE == "#2d2d2d"
        assert DarkTheme.TEXT == "#e0e0e0"
        assert DarkTheme.TEXT_SECONDARY == "#a0a0a0"
        assert DarkTheme.ACCENT == "#007acc"
        assert DarkTheme.SUCCESS == "#4caf50"
        assert DarkTheme.ERROR == "#f44336"
        assert DarkTheme.WARNING == "#ff9800"
        assert DarkTheme.BORDER == "#404040"
        assert DarkTheme.HOVER == "#3d3d3d"
        assert DarkTheme.PRESSED == "#4d4d4d"
        assert DarkTheme.DISABLED == "#606060"

    def test_color_constants_are_valid_hex(self) -> None:
        """Test that all color constants are valid hex colors."""
        color_attrs: list[str] = [
            "BACKGROUND",
            "SURFACE",
            "TEXT",
            "TEXT_SECONDARY",
            "ACCENT",
            "SUCCESS",
            "ERROR",
            "WARNING",
            "BORDER",
            "HOVER",
            "PRESSED",
            "DISABLED",
        ]

        for attr in color_attrs:
            color = getattr(DarkTheme, attr)
            assert color.startswith("#"), f"{attr} should start with #"
            assert len(color) == 7, f"{attr} should be 7 characters long"
            # Should be valid hex
            int(color[1:], 16)  # This will raise ValueError if not valid hex

    @patch("PyQt6.QtWidgets.QApplication.setStyle")
    @patch("PyQt6.QtWidgets.QApplication.setPalette")
    @patch("PyQt6.QtWidgets.QApplication.setStyleSheet")
    def test_apply_theme(self, mock_set_stylesheet: MagicMock, mock_set_palette: MagicMock, mock_set_style: MagicMock) -> None:  # noqa: ARG002
        """Test theme application to QApplication."""
        app: MagicMock = MagicMock(spec=QApplication)

        DarkTheme.apply_theme(app)

        # Verify method calls
        app.setStyle.assert_called_once_with("Fusion")
        app.setPalette.assert_called_once()
        app.setStyleSheet.assert_called_once()

    def test_palette_configuration(self) -> None:
        """Test that palette is configured correctly."""
        with patch("PyQt6.QtWidgets.QApplication") as mock_app_class:
            mock_app: MagicMock = MagicMock()
            mock_app_class.return_value = mock_app

            DarkTheme.apply_theme(mock_app)

            # Verify setPalette was called
            assert mock_app.setPalette.called

            # Get the palette that was set
            palette_call = mock_app.setPalette.call_args[0][0]
            assert isinstance(palette_call, QPalette)

    def test_get_stylesheet_returns_string(self) -> None:
        """Test that _get_stylesheet returns a non-empty string."""
        stylesheet = DarkTheme._get_stylesheet()

        assert isinstance(stylesheet, str)
        assert len(stylesheet) > 0
        assert "QWidget" in stylesheet
        assert "QMenuBar" in stylesheet
        assert "QPushButton" in stylesheet

    def test_stylesheet_contains_theme_colors(self) -> None:
        """Test that stylesheet contains theme color references."""
        stylesheet = DarkTheme._get_stylesheet()

        # Should contain commonly used color constants
        assert DarkTheme.SURFACE in stylesheet
        assert DarkTheme.BORDER in stylesheet
        assert DarkTheme.ACCENT in stylesheet
        assert DarkTheme.BACKGROUND in stylesheet
        assert DarkTheme.TEXT in stylesheet
        assert DarkTheme.HOVER in stylesheet
        assert DarkTheme.PRESSED in stylesheet
        assert DarkTheme.DISABLED in stylesheet

    def test_stylesheet_widget_styling(self) -> None:
        """Test that stylesheet includes styling for major widget types."""
        stylesheet = DarkTheme._get_stylesheet()

        # Test for major widget selectors
        expected_selectors = [
            "QWidget",
            "QMenuBar",
            "QMenu",
            "QPushButton",
            "QLineEdit",
            "QComboBox",
            "QLabel",
            "QStatusBar",
            "QScrollBar",
            "QToolTip",
            "QGroupBox",
            "QProgressBar",
            "QTabWidget",
            "QTextEdit",
        ]

        for selector in expected_selectors:
            assert selector in stylesheet, f"Missing selector: {selector}"

    def test_stylesheet_pseudo_states(self) -> None:
        """Test that stylesheet includes pseudo-state styling."""
        stylesheet = DarkTheme._get_stylesheet()

        # Test for common pseudo-states
        pseudo_states = [":hover", ":pressed", ":disabled", ":focus", ":selected"]

        for state in pseudo_states:
            assert state in stylesheet, f"Missing pseudo-state: {state}"

    def test_qcolor_creation_from_constants(self) -> None:
        """Test that QColor can be created from theme constants."""
        # This tests that our color constants are valid for PyQt6
        colors_to_test = [DarkTheme.BACKGROUND, DarkTheme.SURFACE, DarkTheme.TEXT, DarkTheme.ACCENT, DarkTheme.SUCCESS, DarkTheme.ERROR]

        for color_str in colors_to_test:
            color = QColor(color_str)
            assert color.isValid(), f"Invalid color: {color_str}"

    def test_apply_theme_with_none_app(self) -> None:
        """Test that apply_theme handles None app gracefully."""
        # This should not raise an exception
        with pytest.raises(AttributeError):
            DarkTheme.apply_theme(None)  # type: ignore[arg-type]

    def test_stylesheet_structure(self) -> None:
        """Test that stylesheet has proper CSS structure."""
        stylesheet = DarkTheme._get_stylesheet()

        # Should contain CSS braces
        assert "{" in stylesheet
        assert "}" in stylesheet

        # Should contain CSS properties
        assert "background-color" in stylesheet
        assert "color" in stylesheet
        assert "border" in stylesheet
        assert "padding" in stylesheet

    def test_all_constants_accessible(self) -> None:
        """Test that all color constants are accessible as class attributes."""
        expected_constants = [
            "BACKGROUND",
            "SURFACE",
            "TEXT",
            "TEXT_SECONDARY",
            "ACCENT",
            "SUCCESS",
            "ERROR",
            "WARNING",
            "BORDER",
            "HOVER",
            "PRESSED",
            "DISABLED",
        ]

        for constant in expected_constants:
            assert hasattr(DarkTheme, constant), f"Missing constant: {constant}"
            value = getattr(DarkTheme, constant)
            assert isinstance(value, str), f"{constant} should be a string"
