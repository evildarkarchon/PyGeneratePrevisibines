"""Build controls widget for PyGeneratePrevisibines GUI."""

from typing import Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from PrevisLib.models.data_classes import BuildMode, BuildStep
from gui.styles.dark_theme import DarkTheme


class BuildControlsWidget(QWidget):
    """Widget for controlling the build process."""
    
    # Signals
    buildStarted = pyqtSignal(BuildMode, BuildStep)  # mode, starting_step
    buildStopped = pyqtSignal()
    
    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the build controls widget.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._is_building = False
        self._init_ui()
    
    def _init_ui(self) -> None:
        """Initialize the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)
        
        # Build configuration group
        config_group = QGroupBox("Build Configuration")
        config_layout = QGridLayout(config_group)
        config_layout.setSpacing(10)
        
        # Build mode selector
        mode_label = QLabel("Build Mode:")
        config_layout.addWidget(mode_label, 0, 0)
        
        self.mode_combo = QComboBox()
        self.mode_combo.setMinimumWidth(200)
        for mode in BuildMode:
            self.mode_combo.addItem(mode.value.title(), mode)
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        self.mode_combo.setToolTip(
            "Clean: Full rebuild from scratch\n"
            "Filtered: Resume from filtered cells step\n"
            "Xbox: Optimized build for Xbox platform"
        )
        config_layout.addWidget(self.mode_combo, 0, 1)
        
        # Build step selector
        step_label = QLabel("Starting Step:")
        config_layout.addWidget(step_label, 1, 0)
        
        self.step_combo = QComboBox()
        self.step_combo.setMinimumWidth(200)
        self._populate_steps()
        self.step_combo.setToolTip(
            "Select which step to start from.\n"
            "Useful for resuming interrupted builds."
        )
        config_layout.addWidget(self.step_combo, 1, 1)
        
        # Set column stretch
        config_layout.setColumnStretch(1, 1)
        
        main_layout.addWidget(config_group)
        
        # Build control buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Start/Stop button
        self.start_stop_button = QPushButton("Start Build")
        self.start_stop_button.setMinimumHeight(40)
        self.start_stop_button.clicked.connect(self._on_start_stop_clicked)
        self.start_stop_button.setToolTip("Start or stop the build process")
        
        # Style the button
        self._update_button_style()
        
        button_layout.addWidget(self.start_stop_button)
        
        main_layout.addLayout(button_layout)
    
    def _populate_steps(self) -> None:
        """Populate the step combo box based on current mode."""
        self.step_combo.clear()
        
        current_mode = self.get_build_mode()
        
        # Add all steps
        for step in BuildStep:
            # CompressPSG and BuildCDX are only available in Clean mode
            if step in (BuildStep.COMPRESS_PSG, BuildStep.BUILD_CDX) and current_mode != BuildMode.CLEAN:
                continue
            
            self.step_combo.addItem(str(step), step)
        
        # Default to first step
        self.step_combo.setCurrentIndex(0)
    
    def _on_mode_changed(self) -> None:
        """Handle build mode changes."""
        # Repopulate steps based on new mode
        self._populate_steps()
        
        # Reset to appropriate default step based on mode
        current_mode = self.get_build_mode()
        if current_mode != BuildMode.CLEAN:
            # For filtered mode, default to COMPRESS_PSG equivalent position
            # Since COMPRESS_PSG is skipped, this would be GENERATE_PREVIS
            for i in range(self.step_combo.count()):
                if self.step_combo.itemData(i) == BuildStep.GENERATE_PREVIS:
                    self.step_combo.setCurrentIndex(i)
                    break
    
    def _on_start_stop_clicked(self) -> None:
        """Handle start/stop button clicks."""
        if self._is_building:
            # Stop build
            self.buildStopped.emit()
        else:
            # Start build
            mode = self.get_build_mode()
            step = self.get_build_step()
            self.buildStarted.emit(mode, step)
    
    def _update_button_style(self) -> None:
        """Update the start/stop button style based on state."""
        if self._is_building:
            self.start_stop_button.setText("Stop Build")
            self.start_stop_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {DarkTheme.ERROR};
                    color: white;
                    border: 1px solid {DarkTheme.ERROR};
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: #d32f2f;
                    border-color: #d32f2f;
                }}
                QPushButton:pressed {{
                    background-color: #b71c1c;
                }}
            """)
        else:
            self.start_stop_button.setText("Start Build")
            self.start_stop_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {DarkTheme.SUCCESS};
                    color: white;
                    border: 1px solid {DarkTheme.SUCCESS};
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: #45a049;
                    border-color: #45a049;
                }}
                QPushButton:pressed {{
                    background-color: #2e7d32;
                }}
                QPushButton:disabled {{
                    background-color: {DarkTheme.DISABLED};
                    color: {DarkTheme.TEXT_SECONDARY};
                    border-color: {DarkTheme.DISABLED};
                }}
            """)
    
    def get_build_mode(self) -> BuildMode:
        """Get the currently selected build mode.
        
        Returns:
            Selected build mode
        """
        return self.mode_combo.currentData()
    
    def get_build_step(self) -> BuildStep:
        """Get the currently selected build step.
        
        Returns:
            Selected build step
        """
        return self.step_combo.currentData()
    
    def set_build_mode(self, mode: BuildMode) -> None:
        """Set the build mode.
        
        Args:
            mode: Build mode to set
        """
        for i in range(self.mode_combo.count()):
            if self.mode_combo.itemData(i) == mode:
                self.mode_combo.setCurrentIndex(i)
                break
    
    def set_build_step(self, step: BuildStep) -> None:
        """Set the build step.
        
        Args:
            step: Build step to set
        """
        for i in range(self.step_combo.count()):
            if self.step_combo.itemData(i) == step:
                self.step_combo.setCurrentIndex(i)
                break
    
    def set_building_state(self, is_building: bool) -> None:
        """Set the building state and update UI accordingly.
        
        Args:
            is_building: Whether a build is in progress
        """
        self._is_building = is_building
        
        # Update button
        self._update_button_style()
        
        # Disable/enable controls
        self.mode_combo.setEnabled(not is_building)
        self.step_combo.setEnabled(not is_building)
    
    def setEnabled(self, enabled: bool) -> None:
        """Enable or disable the entire widget.
        
        Args:
            enabled: Whether to enable the widget
        """
        super().setEnabled(enabled)
        
        # Only enable controls if not building
        if enabled and not self._is_building:
            self.mode_combo.setEnabled(True)
            self.step_combo.setEnabled(True)
            self.start_stop_button.setEnabled(True)
        elif not enabled:
            self.mode_combo.setEnabled(False)
            self.step_combo.setEnabled(False)
            self.start_stop_button.setEnabled(False)