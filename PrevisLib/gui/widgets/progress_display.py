"""Progress display widget for PyGeneratePrevisibines GUI."""

from datetime import datetime
from enum import Enum, auto

from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from PrevisLib.gui.styles.dark_theme import DarkTheme
from PrevisLib.models.data_classes import BuildStep


class StepStatus(Enum):
    """Status of a build step."""

    PENDING = auto()
    RUNNING = auto()
    SUCCESS = auto()
    FAILED = auto()


class ProgressDisplayWidget(QWidget):
    """Widget for displaying build progress."""

    # Signal emitted when user confirms cancellation
    cancelConfirmed = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the progress display widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._step_statuses: dict[BuildStep, StepStatus] = {}
        self._start_time: datetime | None = None
        self._current_step: BuildStep | None = None
        self._timer = QTimer()
        self._timer.timeout.connect(self._update_elapsed_time)

        self._init_ui()
        self._reset_progress()

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(15)

        # Current step display
        self.current_step_label = QLabel("Ready to build")
        self.current_step_label.setStyleSheet(f"""
            QLabel {{
                font-size: 18px;
                font-weight: bold;
                color: {DarkTheme.TEXT};
                padding: 10px;
                background-color: {DarkTheme.SURFACE};
                border: 1px solid {DarkTheme.BORDER};
                border-radius: 6px;
            }}
        """)
        main_layout.addWidget(self.current_step_label)

        # Progress info layout
        info_layout = QHBoxLayout()
        info_layout.setSpacing(20)

        # Step counter
        self.step_counter_label = QLabel("Step 0 of 8")
        self.step_counter_label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                color: {DarkTheme.TEXT_SECONDARY};
                font-weight: 500;
            }}
        """)
        info_layout.addWidget(self.step_counter_label)

        # Spacer
        info_layout.addStretch()

        # Time elapsed
        self.time_elapsed_label = QLabel("Time: 00:00:00")
        self.time_elapsed_label.setStyleSheet(f"""
            QLabel {{
                font-size: 14px;
                color: {DarkTheme.TEXT_SECONDARY};
                font-weight: 500;
            }}
        """)
        info_layout.addWidget(self.time_elapsed_label)

        main_layout.addLayout(info_layout)

        # Step list
        self.step_list = QListWidget()
        self.step_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {DarkTheme.SURFACE};
                border: 1px solid {DarkTheme.BORDER};
                border-radius: 4px;
                padding: 5px;
            }}
            QListWidget::item {{
                padding: 8px;
                border: none;
                border-radius: 3px;
                margin: 1px;
            }}
            QListWidget::item:hover {{
                background-color: {DarkTheme.HOVER};
            }}
        """)
        main_layout.addWidget(self.step_list)

        # Initially hide the widget
        self.hide()

    def _reset_progress(self) -> None:
        """Reset the progress display to initial state."""
        # Initialize all steps as pending
        self._step_statuses.clear()
        for step in BuildStep:
            self._step_statuses[step] = StepStatus.PENDING

        self._current_step = None
        self._start_time = None

        # Update UI
        self.current_step_label.setText("Ready to build")
        self.step_counter_label.setText("Step 0 of 8")
        self.time_elapsed_label.setText("Time: 00:00:00")

        # Populate step list
        self._populate_step_list()

    def _populate_step_list(self) -> None:
        """Populate the step list with all build steps."""
        self.step_list.clear()

        for step in BuildStep:
            item = QListWidgetItem()
            item.setText(f"{self._get_status_icon(step)} {step!s}")
            item.setData(256, step)  # Store step as item data
            self.step_list.addItem(item)

    def _get_status_icon(self, step: BuildStep) -> str:
        """Get the status icon for a build step.

        Args:
            step: Build step

        Returns:
            Status icon string
        """
        status = self._step_statuses.get(step, StepStatus.PENDING)

        match status:
            case StepStatus.PENDING:
                return "⏳"
            case StepStatus.RUNNING:
                return "🔄"
            case StepStatus.SUCCESS:
                return "✅"
            case StepStatus.FAILED:
                return "❌"
            case _:
                return "⏳"

    def _get_status_color(self, step: BuildStep) -> str:
        """Get the color for a build step based on its status.

        Args:
            step: Build step

        Returns:
            Color string
        """
        status = self._step_statuses.get(step, StepStatus.PENDING)

        match status:
            case StepStatus.PENDING:
                return DarkTheme.TEXT_SECONDARY
            case StepStatus.RUNNING:
                return DarkTheme.ACCENT
            case StepStatus.SUCCESS:
                return DarkTheme.SUCCESS
            case StepStatus.FAILED:
                return DarkTheme.ERROR
            case _:
                return DarkTheme.TEXT_SECONDARY

    def _update_step_list_item(self, step: BuildStep) -> None:
        """Update a specific step in the list.

        Args:
            step: Build step to update
        """
        for i in range(self.step_list.count()):
            item = self.step_list.item(i)
            if item and item.data(256) == step:
                item.setText(f"{self._get_status_icon(step)} {step!s}")

                # Update item color
                color = self._get_status_color(step)
                item.setForeground(QColor(color))
                break

    def _update_elapsed_time(self) -> None:
        """Update the elapsed time display."""
        if self._start_time:
            elapsed = datetime.now() - self._start_time
            # Format as HH:MM:SS
            total_seconds = int(elapsed.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60

            self.time_elapsed_label.setText(f"Time: {hours:02d}:{minutes:02d}:{seconds:02d}")

    def _get_current_step_number(self) -> int:
        """Get the current step number (1-based).

        Returns:
            Current step number, 0 if no current step
        """
        if not self._current_step:
            return 0

        # Get step index (0-based) and add 1
        steps = list(BuildStep)
        try:
            return steps.index(self._current_step) + 1
        except ValueError:
            return 0

    def start_build(self, starting_step: BuildStep) -> None:
        """Start the build process.

        Args:
            starting_step: Step to start from
        """
        self._start_time = datetime.now()
        self._current_step = starting_step

        # Reset all steps to pending
        for step in BuildStep:
            self._step_statuses[step] = StepStatus.PENDING

        # Set current step to running
        self._step_statuses[starting_step] = StepStatus.RUNNING

        # Update UI
        self.current_step_label.setText(f"Running: {starting_step!s}")
        self.current_step_label.setStyleSheet(f"""
            QLabel {{
                font-size: 18px;
                font-weight: bold;
                color: {DarkTheme.ACCENT};
                padding: 10px;
                background-color: {DarkTheme.SURFACE};
                border: 1px solid {DarkTheme.ACCENT};
                border-radius: 6px;
            }}
        """)

        step_num = self._get_current_step_number()
        self.step_counter_label.setText(f"Step {step_num} of 8")

        # Start timer
        self._timer.start(1000)  # Update every second

        # Update step list
        self._populate_step_list()

        # Show the widget
        self.show()

    def update_step_status(self, step: BuildStep, status: StepStatus) -> None:
        """Update the status of a build step.

        Args:
            step: Build step to update
            status: New status
        """
        self._step_statuses[step] = status

        # Update current step if this is the running step
        if status == StepStatus.RUNNING:
            self._current_step = step
            self.current_step_label.setText(f"Running: {step!s}")
            self.current_step_label.setStyleSheet(f"""
                QLabel {{
                    font-size: 18px;
                    font-weight: bold;
                    color: {DarkTheme.ACCENT};
                    padding: 10px;
                    background-color: {DarkTheme.SURFACE};
                    border: 1px solid {DarkTheme.ACCENT};
                    border-radius: 6px;
                }}
            """)

            step_num = self._get_current_step_number()
            self.step_counter_label.setText(f"Step {step_num} of 8")

        # Update step list
        self._update_step_list_item(step)

    def complete_build(self, success: bool) -> None:
        """Complete the build process.

        Args:
            success: Whether the build completed successfully
        """
        # Stop timer
        self._timer.stop()

        # Update current step label
        if success:
            self.current_step_label.setText("Build completed successfully!")
            self.current_step_label.setStyleSheet(f"""
                QLabel {{
                    font-size: 18px;
                    font-weight: bold;
                    color: {DarkTheme.SUCCESS};
                    padding: 10px;
                    background-color: {DarkTheme.SURFACE};
                    border: 1px solid {DarkTheme.SUCCESS};
                    border-radius: 6px;
                }}
            """)
        else:
            self.current_step_label.setText("Build failed!")
            self.current_step_label.setStyleSheet(f"""
                QLabel {{
                    font-size: 18px;
                    font-weight: bold;
                    color: {DarkTheme.ERROR};
                    padding: 10px;
                    background-color: {DarkTheme.SURFACE};
                    border: 1px solid {DarkTheme.ERROR};
                    border-radius: 6px;
                }}
            """)

        # Update step counter
        if success:
            self.step_counter_label.setText("Step 8 of 8")
        else:
            step_num = self._get_current_step_number()
            self.step_counter_label.setText(f"Failed at step {step_num} of 8")

    def request_cancel(self) -> None:
        """Show cancel confirmation dialog."""
        reply = QMessageBox.question(
            self,
            "Cancel Build",
            "Are you sure you want to cancel the build?\n\n"
            "This will stop the current operation and may leave the build in an incomplete state.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.cancelConfirmed.emit()

    def reset(self) -> None:
        """Reset the progress display and hide it."""
        self._timer.stop()
        self._reset_progress()
        self.hide()
