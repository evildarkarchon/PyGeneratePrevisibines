"""Settings dialog for PyGeneratePrevisibines GUI."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import (
    QButtonGroup,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
)

from PrevisLib.config.settings import Settings
from PrevisLib.models.data_classes import ArchiveTool

if TYPE_CHECKING:
    from loguru import Logger

from PrevisLib.utils.logging import get_logger

logger: Logger = get_logger(__name__)


class SettingsDialog(QDialog):
    """Settings dialog for configuring tool paths and preferences."""

    def __init__(self, parent=None) -> None:
        """Initialize the settings dialog.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Settings for persistence
        self.settings = QSettings("PyGeneratePrevisibines", "SettingsDialog")

        # Current settings instance
        self.current_settings = Settings()

        # UI elements
        self.fallout4_path_edit: QLineEdit
        self.fallout4_path_indicator: QLabel
        self.xedit_path_edit: QLineEdit
        self.xedit_path_indicator: QLabel
        self.bsarch_path_edit: QLineEdit
        self.bsarch_path_indicator: QLabel
        self.archive2_radio: QRadioButton
        self.bsarch_radio: QRadioButton
        self.archive_button_group: QButtonGroup

        # Initialize UI
        self._init_ui()

        # Load current settings
        self._load_settings()

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(600, 400)

        # Main layout
        main_layout = QVBoxLayout(self)

        # Tool paths group
        tool_paths_group = self._create_tool_paths_group()
        main_layout.addWidget(tool_paths_group)

        # Archive tool selection group
        archive_group = self._create_archive_tool_group()
        main_layout.addWidget(archive_group)

        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self._accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def _create_tool_paths_group(self) -> QGroupBox:
        """Create the tool paths configuration group.

        Returns:
            QGroupBox: The tool paths group widget
        """
        group = QGroupBox("Tool Paths")
        layout = QFormLayout(group)

        # Fallout 4 path
        fallout4_layout = QVBoxLayout()
        fallout4_input_layout = QHBoxLayout()

        self.fallout4_path_edit = QLineEdit()
        self.fallout4_path_edit.setPlaceholderText("Path to Fallout4.exe")
        self.fallout4_path_edit.textChanged.connect(self._validate_fallout4_path)

        fallout4_browse_btn = QPushButton("Browse...")
        fallout4_browse_btn.clicked.connect(self._browse_fallout4_path)

        fallout4_input_layout.addWidget(self.fallout4_path_edit)
        fallout4_input_layout.addWidget(fallout4_browse_btn)

        self.fallout4_path_indicator = QLabel()
        self.fallout4_path_indicator.setStyleSheet("color: #666666; font-size: 11px;")

        fallout4_layout.addLayout(fallout4_input_layout)
        fallout4_layout.addWidget(self.fallout4_path_indicator)

        layout.addRow("Fallout 4 Executable:", fallout4_layout)

        # xEdit path
        xedit_layout = QVBoxLayout()
        xedit_input_layout = QHBoxLayout()

        self.xedit_path_edit = QLineEdit()
        self.xedit_path_edit.setPlaceholderText("Path to FO4Edit.exe, xEdit.exe, FO4Edit64.exe, or xEdit64.exe")
        self.xedit_path_edit.textChanged.connect(self._validate_xedit_path)

        xedit_browse_btn = QPushButton("Browse...")
        xedit_browse_btn.clicked.connect(self._browse_xedit_path)

        xedit_input_layout.addWidget(self.xedit_path_edit)
        xedit_input_layout.addWidget(xedit_browse_btn)

        self.xedit_path_indicator = QLabel()
        self.xedit_path_indicator.setStyleSheet("color: #666666; font-size: 11px;")

        xedit_layout.addLayout(xedit_input_layout)
        xedit_layout.addWidget(self.xedit_path_indicator)

        layout.addRow("xEdit Executable:", xedit_layout)

        # BSArch path
        bsarch_layout = QVBoxLayout()
        bsarch_input_layout = QHBoxLayout()

        self.bsarch_path_edit = QLineEdit()
        self.bsarch_path_edit.setPlaceholderText("Path to BSArch.exe (optional)")
        self.bsarch_path_edit.textChanged.connect(self._validate_bsarch_path)

        bsarch_browse_btn = QPushButton("Browse...")
        bsarch_browse_btn.clicked.connect(self._browse_bsarch_path)

        bsarch_input_layout.addWidget(self.bsarch_path_edit)
        bsarch_input_layout.addWidget(bsarch_browse_btn)

        self.bsarch_path_indicator = QLabel()
        self.bsarch_path_indicator.setStyleSheet("color: #666666; font-size: 11px;")

        bsarch_layout.addLayout(bsarch_input_layout)
        bsarch_layout.addWidget(self.bsarch_path_indicator)

        layout.addRow("BSArch Executable:", bsarch_layout)

        return group

    def _create_archive_tool_group(self) -> QGroupBox:
        """Create the archive tool selection group.

        Returns:
            QGroupBox: The archive tool group widget
        """
        group = QGroupBox("Archive Tool Preference")
        layout = QVBoxLayout(group)

        # Radio buttons for archive tool selection
        self.archive2_radio = QRadioButton("Archive2 (Bethesda's official tool)")
        self.bsarch_radio = QRadioButton("BSArch (Third-party alternative)")

        # Button group to ensure mutual exclusion
        self.archive_button_group = QButtonGroup()
        self.archive_button_group.addButton(self.archive2_radio, 0)
        self.archive_button_group.addButton(self.bsarch_radio, 1)

        layout.addWidget(self.archive2_radio)
        layout.addWidget(self.bsarch_radio)

        # Set default selection
        self.archive2_radio.setChecked(True)

        return group

    def _load_settings(self) -> None:
        """Load current settings into the dialog."""
        try:
            # Load tool paths if available
            if self.current_settings.tool_paths.fallout4:
                self.fallout4_path_edit.setText(str(self.current_settings.tool_paths.fallout4))

            if self.current_settings.tool_paths.xedit:
                self.xedit_path_edit.setText(str(self.current_settings.tool_paths.xedit))

            if self.current_settings.tool_paths.bsarch:
                self.bsarch_path_edit.setText(str(self.current_settings.tool_paths.bsarch))

            # Set archive tool preference
            if self.current_settings.archive_tool == ArchiveTool.BSARCH:
                self.bsarch_radio.setChecked(True)
            else:
                self.archive2_radio.setChecked(True)

        except Exception as e:
            logger.warning(f"Failed to load current settings: {e}")

    def _browse_fallout4_path(self) -> None:
        """Open file dialog to browse for Fallout 4 executable."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Fallout 4 Executable", "", "Executable Files (*.exe);;All Files (*)")

        if file_path:
            self.fallout4_path_edit.setText(file_path)

    def _browse_xedit_path(self) -> None:
        """Open file dialog to browse for xEdit executable."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select xEdit Executable", "", "Executable Files (*.exe);;All Files (*)")

        if file_path:
            self.xedit_path_edit.setText(file_path)

    def _browse_bsarch_path(self) -> None:
        """Open file dialog to browse for BSArch executable."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select BSArch Executable", "", "Executable Files (*.exe);;All Files (*)")

        if file_path:
            self.bsarch_path_edit.setText(file_path)

    def _validate_fallout4_path(self) -> None:
        """Validate the Fallout 4 path."""
        path_text = self.fallout4_path_edit.text().strip()

        if not path_text:
            self.fallout4_path_indicator.setText("")
            return

        path = Path(path_text)

        if not path.exists():
            self.fallout4_path_indicator.setText("❌ File does not exist")
            self.fallout4_path_indicator.setStyleSheet("color: #f44336; font-size: 11px;")
        elif not path.name.lower() == "fallout4.exe":
            self.fallout4_path_indicator.setText("⚠️ Should be Fallout4.exe")
            self.fallout4_path_indicator.setStyleSheet("color: #ff9800; font-size: 11px;")
        else:
            self.fallout4_path_indicator.setText("✓ Valid Fallout 4 executable")
            self.fallout4_path_indicator.setStyleSheet("color: #4caf50; font-size: 11px;")

    def _validate_xedit_path(self) -> None:
        """Validate the xEdit path."""
        path_text = self.xedit_path_edit.text().strip()

        if not path_text:
            self.xedit_path_indicator.setText("")
            return

        path = Path(path_text)

        if not path.exists():
            self.xedit_path_indicator.setText("❌ File does not exist")
            self.xedit_path_indicator.setStyleSheet("color: #f44336; font-size: 11px;")
        elif path.name.lower() not in ["fo4edit.exe", "xedit.exe", "fo4edit64.exe", "xedit64.exe"]:
            self.xedit_path_indicator.setText("⚠️ Should be FO4Edit.exe, xEdit.exe, FO4Edit64.exe, or xEdit64.exe")
            self.xedit_path_indicator.setStyleSheet("color: #ff9800; font-size: 11px;")
        else:
            self.xedit_path_indicator.setText("✓ Valid xEdit executable")
            self.xedit_path_indicator.setStyleSheet("color: #4caf50; font-size: 11px;")

    def _validate_bsarch_path(self) -> None:
        """Validate the BSArch path."""
        path_text = self.bsarch_path_edit.text().strip()

        if not path_text:
            self.bsarch_path_indicator.setText("Optional - leave blank to use Archive2")
            self.bsarch_path_indicator.setStyleSheet("color: #666666; font-size: 11px;")
            return

        path = Path(path_text)

        if not path.exists():
            self.bsarch_path_indicator.setText("❌ File does not exist")
            self.bsarch_path_indicator.setStyleSheet("color: #f44336; font-size: 11px;")
        elif not path.name.lower() == "bsarch.exe":
            self.bsarch_path_indicator.setText("⚠️ Should be BSArch.exe")
            self.bsarch_path_indicator.setStyleSheet("color: #ff9800; font-size: 11px;")
        else:
            self.bsarch_path_indicator.setText("✓ Valid BSArch executable")
            self.bsarch_path_indicator.setStyleSheet("color: #4caf50; font-size: 11px;")

    def _validate_all_paths(self) -> tuple[bool, list[str]]:
        """Validate all paths and return validation status.

        Returns:
            tuple[bool, list[str]]: (is_valid, error_messages)
        """
        errors: list[str] = []

        # Validate Fallout 4 path (required)
        fallout4_path = self.fallout4_path_edit.text().strip()
        if not fallout4_path:
            errors.append("Fallout 4 path is required")
        elif not Path(fallout4_path).exists():
            errors.append("Fallout 4 executable does not exist")

        # Validate xEdit path (required)
        xedit_path = self.xedit_path_edit.text().strip()
        if not xedit_path:
            errors.append("xEdit path is required")
        elif not Path(xedit_path).exists():
            errors.append("xEdit executable does not exist")

        # Validate BSArch path (optional, but if provided must be valid)
        bsarch_path = self.bsarch_path_edit.text().strip()
        if bsarch_path and not Path(bsarch_path).exists():
            errors.append("BSArch executable does not exist")

        return len(errors) == 0, errors

    def _accept(self) -> None:
        """Accept the dialog and save settings."""
        is_valid, errors = self._validate_all_paths()

        if not is_valid:
            from PyQt6.QtWidgets import QMessageBox

            error_message = "Please fix the following issues:\n\n" + "\n".join(f"• {error}" for error in errors)
            QMessageBox.warning(self, "Invalid Settings", error_message)
            return

        # Save settings to current_settings instance
        self._save_settings()

        # Accept the dialog
        self.accept()

    def _save_settings(self) -> None:
        """Save the current dialog settings."""
        try:
            # Update tool paths
            fallout4_path = self.fallout4_path_edit.text().strip()
            if fallout4_path:
                self.current_settings.tool_paths.fallout4 = Path(fallout4_path)

                # Auto-detect Creation Kit if in same directory
                ck_path = Path(fallout4_path).parent / "CreationKit.exe"
                if ck_path.exists():
                    self.current_settings.tool_paths.creation_kit = ck_path

                # Auto-detect Archive2 if in tools directory
                archive2_path = Path(fallout4_path).parent / "Tools" / "Archive2" / "Archive2.exe"
                if archive2_path.exists():
                    self.current_settings.tool_paths.archive2 = archive2_path

            xedit_path = self.xedit_path_edit.text().strip()
            if xedit_path:
                self.current_settings.tool_paths.xedit = Path(xedit_path)

            bsarch_path = self.bsarch_path_edit.text().strip()
            if bsarch_path:
                self.current_settings.tool_paths.bsarch = Path(bsarch_path)

            # Update archive tool preference
            if self.bsarch_radio.isChecked():
                self.current_settings.archive_tool = ArchiveTool.BSARCH
            else:
                self.current_settings.archive_tool = ArchiveTool.ARCHIVE2

            logger.info("Settings saved successfully")

        except Exception as e:
            logger.error(f"Failed to save settings: {e}")

    def get_settings(self) -> Settings:
        """Get the current settings instance.

        Returns:
            Settings: The current settings
        """
        return self.current_settings
