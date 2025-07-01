"""Plugin input widget for PyGeneratePrevisibines GUI."""

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QPalette
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from PrevisLib.config.settings import Settings
from PrevisLib.utils.validation import validate_plugin_name
from gui.styles.dark_theme import DarkTheme


class PluginInputWidget(QWidget):
    """Widget for entering and validating plugin names."""
    
    # Signal emitted when validation state changes
    validationStateChanged = pyqtSignal(bool, str)  # is_valid, message
    
    def __init__(self, settings: Optional[Settings] = None, parent: Optional[QWidget] = None) -> None:
        """Initialize the plugin input widget.
        
        Args:
            settings: Optional settings object for checking plugin existence
            parent: Parent widget
        """
        super().__init__(parent)
        self.settings = settings
        self._validation_timer = QTimer()
        self._validation_timer.setSingleShot(True)
        self._validation_timer.timeout.connect(self._validate_plugin)
        
        self._init_ui()
    
    def _init_ui(self) -> None:
        """Initialize the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(5)
        
        # Input row layout
        input_layout = QHBoxLayout()
        input_layout.setSpacing(10)
        
        # Plugin name label
        self.label = QLabel("Plugin Name:")
        input_layout.addWidget(self.label)
        
        # Plugin name input
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText("Enter plugin name (e.g., MyMod or MyMod.esp)")
        self.line_edit.textChanged.connect(self._on_text_changed)
        input_layout.addWidget(self.line_edit, 1)
        
        # Validation indicator
        self.validation_icon = QLabel()
        self.validation_icon.setFixedSize(20, 20)
        input_layout.addWidget(self.validation_icon)
        
        main_layout.addLayout(input_layout)
        
        # Validation message label
        self.validation_message = QLabel()
        self.validation_message.setWordWrap(True)
        self.validation_message.setStyleSheet(f"QLabel {{ padding: 2px 5px; }}")
        self.validation_message.hide()
        main_layout.addWidget(self.validation_message)
        
        # Add tooltip
        self.line_edit.setToolTip(
            "Enter the name of your plugin.\n"
            "The .esp extension will be added automatically if not provided.\n"
            "Plugin names cannot contain spaces or be reserved names."
        )
    
    def _on_text_changed(self, text: str) -> None:
        """Handle text changes in the line edit.
        
        Args:
            text: Current text in the line edit
        """
        # Reset validation timer to debounce validation
        self._validation_timer.stop()
        self._validation_timer.start(300)  # 300ms delay
        
        # Clear validation while typing
        self.validation_icon.clear()
        self.validation_message.hide()
    
    def _validate_plugin(self) -> None:
        """Validate the current plugin name."""
        plugin_name = self.line_edit.text().strip()
        
        # Empty name is considered invalid but don't show error
        if not plugin_name:
            self._set_validation_state(False, "")
            return
        
        # Auto-append .esp if no extension
        if "." not in plugin_name:
            plugin_name += ".esp"
            # Update the line edit to show the full name
            self.line_edit.blockSignals(True)
            self.line_edit.setText(plugin_name)
            self.line_edit.blockSignals(False)
        
        # Basic validation
        is_valid, error_message = validate_plugin_name(plugin_name)
        
        if is_valid:
            # Check for additional reserved names
            reserved_build_names = {"previs", "combinedobjects", "xprevispatch"}
            plugin_base = Path(plugin_name).stem.lower()
            if plugin_base in reserved_build_names:
                is_valid = False
                error_message = f"Plugin name '{plugin_base}' is reserved for internal use"
        
        if is_valid and self.settings and self.settings.tool_paths.fallout4:
            # Check if plugin exists
            data_path = self.settings.tool_paths.fallout4 / "Data"
            plugin_path = data_path / plugin_name
            
            if plugin_path.exists():
                self._set_validation_state(True, f"Plugin exists: {plugin_name}", exists=True)
            else:
                # Check if archive exists
                archive_name = f"{Path(plugin_name).stem} - Main.ba2"
                archive_path = data_path / archive_name
                
                if archive_path.exists():
                    self._set_validation_state(
                        False, 
                        f"Archive '{archive_name}' already exists. Choose a different plugin name.",
                        exists=False
                    )
                else:
                    self._set_validation_state(
                        True, 
                        f"Plugin does not exist and will be created: {plugin_name}",
                        exists=False
                    )
        else:
            self._set_validation_state(is_valid, error_message or "Plugin name is valid")
    
    def _set_validation_state(self, is_valid: bool, message: str, exists: Optional[bool] = None) -> None:
        """Set the validation state and update UI.
        
        Args:
            is_valid: Whether the plugin name is valid
            message: Validation message to display
            exists: Whether the plugin exists (None if unknown)
        """
        # Update validation icon
        if is_valid:
            if exists is True:
                # Green check for existing plugin
                self.validation_icon.setText("✓")
                self.validation_icon.setStyleSheet(f"QLabel {{ color: {DarkTheme.SUCCESS}; font-weight: bold; }}")
            elif exists is False:
                # Blue info icon for new plugin
                self.validation_icon.setText("ℹ")
                self.validation_icon.setStyleSheet(f"QLabel {{ color: {DarkTheme.ACCENT}; font-weight: bold; }}")
            else:
                # Green check for valid name (existence unknown)
                self.validation_icon.setText("✓")
                self.validation_icon.setStyleSheet(f"QLabel {{ color: {DarkTheme.SUCCESS}; font-weight: bold; }}")
        else:
            # Red X for invalid
            self.validation_icon.setText("✗")
            self.validation_icon.setStyleSheet(f"QLabel {{ color: {DarkTheme.ERROR}; font-weight: bold; }}")
        
        # Update validation message
        if message:
            self.validation_message.setText(message)
            if is_valid:
                if exists is False:
                    # Info style for new plugin
                    self.validation_message.setStyleSheet(
                        f"QLabel {{ color: {DarkTheme.ACCENT}; background-color: rgba(0, 122, 204, 0.2); "
                        f"border: 1px solid {DarkTheme.ACCENT}; border-radius: 3px; padding: 2px 5px; }}"
                    )
                else:
                    # Success style
                    self.validation_message.setStyleSheet(
                        f"QLabel {{ color: {DarkTheme.SUCCESS}; background-color: rgba(76, 175, 80, 0.2); "
                        f"border: 1px solid {DarkTheme.SUCCESS}; border-radius: 3px; padding: 2px 5px; }}"
                    )
            else:
                # Error style
                self.validation_message.setStyleSheet(
                    f"QLabel {{ color: {DarkTheme.ERROR}; background-color: rgba(244, 67, 54, 0.2); "
                    f"border: 1px solid {DarkTheme.ERROR}; border-radius: 3px; padding: 2px 5px; }}"
                )
            self.validation_message.show()
        else:
            self.validation_message.hide()
        
        # Emit signal
        self.validationStateChanged.emit(is_valid, message)
    
    def get_plugin_name(self) -> str:
        """Get the current plugin name with extension.
        
        Returns:
            Plugin name with extension, or empty string if invalid
        """
        plugin_name = self.line_edit.text().strip()
        if plugin_name and "." not in plugin_name:
            plugin_name += ".esp"
        return plugin_name
    
    def set_plugin_name(self, plugin_name: str) -> None:
        """Set the plugin name.
        
        Args:
            plugin_name: Plugin name to set
        """
        self.line_edit.setText(plugin_name)
    
    def is_valid(self) -> bool:
        """Check if the current plugin name is valid.
        
        Returns:
            True if valid, False otherwise
        """
        plugin_name = self.get_plugin_name()
        if not plugin_name:
            return False
        
        is_valid, _ = validate_plugin_name(plugin_name)
        
        # Check additional reserved names
        if is_valid:
            reserved_build_names = {"previs", "combinedobjects", "xprevispatch"}
            plugin_base = Path(plugin_name).stem.lower()
            if plugin_base in reserved_build_names:
                is_valid = False
        
        return is_valid
    
    def update_settings(self, settings: Settings) -> None:
        """Update the settings object used for validation.
        
        Args:
            settings: New settings object
        """
        self.settings = settings
        # Re-validate with new settings
        if self.line_edit.text():
            self._validate_plugin()