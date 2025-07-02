"""Build thread for executing previs build process in background."""


from loguru import logger
from PyQt6.QtCore import QThread, pyqtSignal

from PrevisLib.config.settings import Settings
from PrevisLib.core.builder import PrevisBuilder
from PrevisLib.models.data_classes import BuildStatus, BuildStep


class BuildThread(QThread):
    """Thread for running the previs build process."""
    
    # Signals
    step_started = pyqtSignal(BuildStep)
    step_progress = pyqtSignal(BuildStep, int, str)  # step, percentage, message
    step_completed = pyqtSignal(BuildStep)
    build_completed = pyqtSignal()
    build_failed = pyqtSignal(BuildStep, str)  # failed_step, error_message
    log_message = pyqtSignal(str, str, str)  # timestamp, level, message
    
    def __init__(self, settings: Settings, start_from_step: BuildStep | None = None) -> None:
        """Initialize build thread.
        
        Args:
            settings: Build settings including plugin name and paths
            start_from_step: Optional step to start from
        """
        super().__init__()
        self.settings = settings
        self.start_from_step = start_from_step
        self.builder: PrevisBuilder | None = None
        self._cancelled = False
        
    def run(self) -> None:
        """Execute the build process."""
        try:
            # Create builder with progress callback
            self.builder = PrevisBuilder(self.settings)
            
            # Set up progress callback
            self.builder.progress_callback = self._progress_callback
            
            # Hook into logger to capture messages
            logger.add(self._log_handler, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", catch=True)
            
            # Run the build
            success = self.builder.build(self.start_from_step)
            
            if success:
                self.build_completed.emit()
            else:
                failed_step = self.builder.failed_step or BuildStep.GENERATE_PRECOMBINED
                self.build_failed.emit(failed_step, "Build process failed")
                
        except Exception as e:  # noqa: BLE001
            logger.exception("Build thread encountered an error")
            failed_step = self.builder.current_step if self.builder else BuildStep.GENERATE_PRECOMBINED
            self.build_failed.emit(failed_step, str(e))
            
    def cancel(self) -> None:
        """Request cancellation of the build process."""
        self._cancelled = True
        if self.builder:
            self.builder.cancel_requested = True
            
    def _progress_callback(self, step: BuildStep, status: BuildStatus, message: str) -> None:
        """Handle progress updates from the builder.
        
        Args:
            step: Current build step
            status: Status of the step
            message: Progress message
        """
        if self._cancelled:
            return
            
        if status == BuildStatus.RUNNING:
            self.step_started.emit(step)
        elif status == BuildStatus.COMPLETED:
            self.step_completed.emit(step)
        elif status == BuildStatus.FAILED:
            self.build_failed.emit(step, message)
            
        # For now, emit generic progress (can be enhanced later with actual percentages)
        if status == BuildStatus.RUNNING and message:
            self.step_progress.emit(step, 0, message)
            
    def _log_handler(self, message: dict) -> None:  # type: ignore[arg-type]
        """Handle log messages from loguru.
        
        Args:
            message: Log message dictionary from loguru
        """
        if self._cancelled:
            return
            
        timestamp = message["time"].strftime("%Y-%m-%d %H:%M:%S")
        level = message["level"].name
        text = message["message"]
        
        self.log_message.emit(timestamp, level, text)