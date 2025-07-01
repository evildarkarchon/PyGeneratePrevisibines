"""Tests for SettingsDialog GUI component."""

from __future__ import annotations

from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication, QDialogButtonBox, QMessageBox

from PrevisLib.gui.settings_dialog import SettingsDialog
from PrevisLib.models.data_classes import ArchiveTool


class TestSettingsDialog:
    """Test SettingsDialog functionality."""

    @pytest.fixture
    def app(self) -> QApplication:
        """Create QApplication instance for testing."""
        app = QApplication.instance()
        if isinstance(app, QApplication):
            return app
        return QApplication([])

    @pytest.fixture
    def dialog(self, app: QApplication) -> Generator[SettingsDialog, None, None]:
        """Create SettingsDialog instance for testing."""
        # Use context manager to patch at class level to avoid dialog showing
        with patch("PyQt6.QtWidgets.QDialog.show"), patch("PyQt6.QtWidgets.QDialog.exec", return_value=0):
            dialog = SettingsDialog()

            # Ensure dialog cleanup after test
            yield dialog

        # Final cleanup: Close dialog if it's still open
        if dialog.isVisible():
            dialog.close()

        # Process any pending events to ensure cleanup
        app.processEvents()

    @pytest.fixture
    def mock_paths(self, tmp_path: Path) -> dict[str, Path]:
        """Create mock executable paths for testing."""
        fallout4_exe = tmp_path / "Fallout4.exe"
        xedit_exe = tmp_path / "FO4Edit.exe"
        bsarch_exe = tmp_path / "BSArch.exe"

        # Create the files
        fallout4_exe.touch()
        xedit_exe.touch()
        bsarch_exe.touch()

        return {
            "fallout4": fallout4_exe,
            "xedit": xedit_exe,
            "bsarch": bsarch_exe,
        }

    def test_dialog_initialization(self, dialog: SettingsDialog) -> None:
        """Test dialog initialization."""
        assert dialog.windowTitle() == "Settings"
        assert dialog.isModal()
        assert dialog.fallout4_path_edit is not None
        assert dialog.xedit_path_edit is not None
        assert dialog.bsarch_path_edit is not None
        assert dialog.archive2_radio is not None
        assert dialog.bsarch_radio is not None

    def test_default_archive_tool_selection(self, dialog: SettingsDialog) -> None:
        """Test that Archive2 is selected by default."""
        assert dialog.archive2_radio.isChecked()
        assert not dialog.bsarch_radio.isChecked()

    def test_path_validation_fallout4_valid(self, dialog: SettingsDialog, mock_paths: dict[str, Path]) -> None:
        """Test Fallout 4 path validation with valid path."""
        dialog.fallout4_path_edit.setText(str(mock_paths["fallout4"]))
        dialog._validate_fallout4_path()

        assert "✓ Valid Fallout 4 executable" in dialog.fallout4_path_indicator.text()
        assert "color: #4caf50" in dialog.fallout4_path_indicator.styleSheet()

    def test_path_validation_fallout4_invalid_file(self, dialog: SettingsDialog, tmp_path: Path) -> None:
        """Test Fallout 4 path validation with invalid filename."""
        invalid_exe = tmp_path / "WrongName.exe"
        invalid_exe.touch()

        dialog.fallout4_path_edit.setText(str(invalid_exe))
        dialog._validate_fallout4_path()

        assert "⚠️ Should be Fallout4.exe" in dialog.fallout4_path_indicator.text()
        assert "color: #ff9800" in dialog.fallout4_path_indicator.styleSheet()

    def test_path_validation_fallout4_nonexistent(self, dialog: SettingsDialog, tmp_path: Path) -> None:
        """Test Fallout 4 path validation with nonexistent file."""
        nonexistent = tmp_path / "DoesNotExist.exe"

        dialog.fallout4_path_edit.setText(str(nonexistent))
        dialog._validate_fallout4_path()

        assert "❌ File does not exist" in dialog.fallout4_path_indicator.text()
        assert "color: #f44336" in dialog.fallout4_path_indicator.styleSheet()

    def test_path_validation_xedit_valid(self, dialog: SettingsDialog, mock_paths: dict[str, Path]) -> None:
        """Test xEdit path validation with valid path."""
        dialog.xedit_path_edit.setText(str(mock_paths["xedit"]))
        dialog._validate_xedit_path()

        assert "✓ Valid xEdit executable" in dialog.xedit_path_indicator.text()
        assert "color: #4caf50" in dialog.xedit_path_indicator.styleSheet()

    def test_path_validation_xedit_invalid_file(self, dialog: SettingsDialog, tmp_path: Path) -> None:
        """Test xEdit path validation with invalid filename."""
        invalid_exe = tmp_path / "WrongEdit.exe"
        invalid_exe.touch()

        dialog.xedit_path_edit.setText(str(invalid_exe))
        dialog._validate_xedit_path()

        assert "⚠️ Should be FO4Edit.exe, xEdit.exe, FO4Edit64.exe, or xEdit64.exe" in dialog.xedit_path_indicator.text()
        assert "color: #ff9800" in dialog.xedit_path_indicator.styleSheet()

    def test_path_validation_bsarch_valid(self, dialog: SettingsDialog, mock_paths: dict[str, Path]) -> None:
        """Test BSArch path validation with valid path."""
        dialog.bsarch_path_edit.setText(str(mock_paths["bsarch"]))
        dialog._validate_bsarch_path()

        assert "✓ Valid BSArch executable" in dialog.bsarch_path_indicator.text()
        assert "color: #4caf50" in dialog.bsarch_path_indicator.styleSheet()

    def test_path_validation_bsarch_empty(self, dialog: SettingsDialog) -> None:
        """Test BSArch path validation with empty path."""
        dialog.bsarch_path_edit.setText("")
        dialog._validate_bsarch_path()

        assert "Optional - leave blank to use Archive2" in dialog.bsarch_path_indicator.text()
        assert "color: #666666" in dialog.bsarch_path_indicator.styleSheet()

    def test_path_validation_bsarch_invalid_file(self, dialog: SettingsDialog, tmp_path: Path) -> None:
        """Test BSArch path validation with invalid filename."""
        invalid_exe = tmp_path / "WrongArch.exe"
        invalid_exe.touch()

        dialog.bsarch_path_edit.setText(str(invalid_exe))
        dialog._validate_bsarch_path()

        assert "⚠️ Should be BSArch.exe" in dialog.bsarch_path_indicator.text()
        assert "color: #ff9800" in dialog.bsarch_path_indicator.styleSheet()

    def test_validate_all_paths_success(self, dialog: SettingsDialog, mock_paths: dict[str, Path]) -> None:
        """Test successful validation of all paths."""
        dialog.fallout4_path_edit.setText(str(mock_paths["fallout4"]))
        dialog.xedit_path_edit.setText(str(mock_paths["xedit"]))
        dialog.bsarch_path_edit.setText(str(mock_paths["bsarch"]))

        is_valid, errors = dialog._validate_all_paths()

        assert is_valid
        assert len(errors) == 0

    def test_validate_all_paths_missing_required(self, dialog: SettingsDialog) -> None:
        """Test validation with missing required paths."""
        # Leave required fields empty
        dialog.fallout4_path_edit.setText("")
        dialog.xedit_path_edit.setText("")

        is_valid, errors = dialog._validate_all_paths()

        assert not is_valid
        assert "Fallout 4 path is required" in errors
        assert "xEdit path is required" in errors

    def test_validate_all_paths_nonexistent_files(self, dialog: SettingsDialog, tmp_path: Path) -> None:
        """Test validation with nonexistent files."""
        dialog.fallout4_path_edit.setText(str(tmp_path / "NoFallout4.exe"))
        dialog.xedit_path_edit.setText(str(tmp_path / "NoEdit.exe"))
        dialog.bsarch_path_edit.setText(str(tmp_path / "NoBSArch.exe"))

        is_valid, errors = dialog._validate_all_paths()

        assert not is_valid
        assert "Fallout 4 executable does not exist" in errors
        assert "xEdit executable does not exist" in errors
        assert "BSArch executable does not exist" in errors

    def test_archive_tool_selection_archive2(self, dialog: SettingsDialog) -> None:
        """Test Archive2 selection."""
        dialog.archive2_radio.setChecked(True)
        dialog._save_settings()

        assert dialog.current_settings.archive_tool == ArchiveTool.ARCHIVE2

    def test_archive_tool_selection_bsarch(self, dialog: SettingsDialog) -> None:
        """Test BSArch selection."""
        dialog.bsarch_radio.setChecked(True)
        dialog._save_settings()

        assert dialog.current_settings.archive_tool == ArchiveTool.BSARCH

    def test_save_settings_with_paths(self, dialog: SettingsDialog, mock_paths: dict[str, Path]) -> None:
        """Test saving settings with valid paths."""
        dialog.fallout4_path_edit.setText(str(mock_paths["fallout4"]))
        dialog.xedit_path_edit.setText(str(mock_paths["xedit"]))
        dialog.bsarch_path_edit.setText(str(mock_paths["bsarch"]))
        dialog.bsarch_radio.setChecked(True)

        dialog._save_settings()

        settings = dialog.get_settings()
        assert settings.tool_paths.fallout4 == mock_paths["fallout4"]
        assert settings.tool_paths.xedit == mock_paths["xedit"]
        assert settings.tool_paths.bsarch == mock_paths["bsarch"]
        assert settings.archive_tool == ArchiveTool.BSARCH

    def test_auto_detect_creation_kit(self, dialog: SettingsDialog, tmp_path: Path) -> None:
        """Test auto-detection of Creation Kit from Fallout 4 path."""
        fallout4_exe = tmp_path / "Fallout4.exe"
        ck_exe = tmp_path / "CreationKit.exe"

        fallout4_exe.touch()
        ck_exe.touch()

        dialog.fallout4_path_edit.setText(str(fallout4_exe))
        dialog._save_settings()

        settings = dialog.get_settings()
        assert settings.tool_paths.creation_kit == ck_exe

    def test_auto_detect_archive2(self, dialog: SettingsDialog, tmp_path: Path) -> None:
        """Test auto-detection of Archive2 from Fallout 4 path."""
        fallout4_exe = tmp_path / "Fallout4.exe"
        tools_dir = tmp_path / "Tools" / "Archive2"
        tools_dir.mkdir(parents=True)
        archive2_exe = tools_dir / "Archive2.exe"

        fallout4_exe.touch()
        archive2_exe.touch()

        dialog.fallout4_path_edit.setText(str(fallout4_exe))
        dialog._save_settings()

        settings = dialog.get_settings()
        assert settings.tool_paths.archive2 == archive2_exe

    @patch("PyQt6.QtWidgets.QMessageBox.warning")
    def test_accept_with_validation_errors(self, mock_warning: MagicMock, dialog: SettingsDialog) -> None:
        """Test that accept shows warning dialog for validation errors."""
        # Set invalid paths
        dialog.fallout4_path_edit.setText("")  # Required but empty
        dialog.xedit_path_edit.setText("")  # Required but empty

        # Ensure the dialog doesn't actually show by mocking the warning
        dialog._accept()

        # Should show warning dialog
        mock_warning.assert_called_once()
        args = mock_warning.call_args[0]
        assert "Invalid Settings" in args[1]
        assert "Fallout 4 path is required" in args[2]
        assert "xEdit path is required" in args[2]

    def test_accept_with_valid_paths(self, dialog: SettingsDialog, mock_paths: dict[str, Path]) -> None:
        """Test successful accept with valid paths."""
        dialog.fallout4_path_edit.setText(str(mock_paths["fallout4"]))
        dialog.xedit_path_edit.setText(str(mock_paths["xedit"]))

        # Mock the accept method to prevent the dialog from actually closing during test
        with patch.object(dialog, "accept") as mock_accept:
            dialog._accept()
            mock_accept.assert_called_once()

    def test_load_settings_from_current(self, dialog: SettingsDialog, mock_paths: dict[str, Path]) -> None:
        """Test loading settings from current settings instance."""
        # Set up current settings
        dialog.current_settings.tool_paths.fallout4 = mock_paths["fallout4"]
        dialog.current_settings.tool_paths.xedit = mock_paths["xedit"]
        dialog.current_settings.tool_paths.bsarch = mock_paths["bsarch"]
        dialog.current_settings.archive_tool = ArchiveTool.BSARCH

        # Reload settings into dialog
        dialog._load_settings()

        assert dialog.fallout4_path_edit.text() == str(mock_paths["fallout4"])
        assert dialog.xedit_path_edit.text() == str(mock_paths["xedit"])
        assert dialog.bsarch_path_edit.text() == str(mock_paths["bsarch"])
        assert dialog.bsarch_radio.isChecked()

    @patch("PrevisLib.gui.settings_dialog.logger")
    def test_save_settings_exception_handling(self, mock_logger: MagicMock, dialog: SettingsDialog) -> None:
        """Test exception handling in save_settings."""
        # Force an exception by setting an invalid path type
        with patch.object(dialog, "fallout4_path_edit") as mock_edit:
            mock_edit.text.return_value.strip.side_effect = Exception("Test error")

            dialog._save_settings()

            # Should log error
            mock_logger.error.assert_called_once()

    def test_browse_dialogs(self, dialog: SettingsDialog, mock_paths: dict[str, Path]) -> None:
        """Test file browse dialogs."""
        with patch("PyQt6.QtWidgets.QFileDialog.getOpenFileName") as mock_dialog:
            mock_dialog.return_value = (str(mock_paths["fallout4"]), "")

            dialog._browse_fallout4_path()
            assert dialog.fallout4_path_edit.text() == str(mock_paths["fallout4"])

            mock_dialog.return_value = (str(mock_paths["xedit"]), "")
            dialog._browse_xedit_path()
            assert dialog.xedit_path_edit.text() == str(mock_paths["xedit"])

            mock_dialog.return_value = (str(mock_paths["bsarch"]), "")
            dialog._browse_bsarch_path()
            assert dialog.bsarch_path_edit.text() == str(mock_paths["bsarch"])

    def test_browse_dialogs_cancelled(self, dialog: SettingsDialog) -> None:
        """Test file browse dialogs when cancelled."""
        with patch("PyQt6.QtWidgets.QFileDialog.getOpenFileName") as mock_dialog:
            mock_dialog.return_value = ("", "")  # User cancelled

            original_text = dialog.fallout4_path_edit.text()
            dialog._browse_fallout4_path()

            # Text should remain unchanged
            assert dialog.fallout4_path_edit.text() == original_text

    def test_dialog_cleanup_after_creation(self, dialog: SettingsDialog) -> None:
        """Test that dialog is properly cleaned up after creation."""
        # Dialog should not be visible by default
        assert not dialog.isVisible()

        # Dialog should be properly initialized
        assert dialog.isModal()
        assert dialog.windowTitle() == "Settings"
