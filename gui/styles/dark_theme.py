"""Dark theme implementation for PyGeneratePrevisibines GUI."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtWidgets import QApplication


class DarkTheme:
    """Dark theme manager for the application."""
    
    # Color palette constants
    BACKGROUND = "#1e1e1e"
    SURFACE = "#2d2d2d"
    TEXT = "#e0e0e0"
    TEXT_SECONDARY = "#a0a0a0"
    ACCENT = "#007acc"
    SUCCESS = "#4caf50"
    ERROR = "#f44336"
    WARNING = "#ff9800"
    BORDER = "#404040"
    HOVER = "#3d3d3d"
    PRESSED = "#4d4d4d"
    DISABLED = "#606060"
    
    @staticmethod
    def apply_theme(app: QApplication) -> None:
        """Apply dark theme to the application."""
        # Set application style
        app.setStyle("Fusion")
        
        # Create and configure palette
        palette = QPalette()
        
        # Window colors
        palette.setColor(QPalette.ColorRole.Window, QColor(DarkTheme.BACKGROUND))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(DarkTheme.TEXT))
        
        # Base colors (for input widgets)
        palette.setColor(QPalette.ColorRole.Base, QColor(DarkTheme.SURFACE))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(DarkTheme.BACKGROUND))
        
        # Text colors
        palette.setColor(QPalette.ColorRole.Text, QColor(DarkTheme.TEXT))
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(DarkTheme.TEXT_SECONDARY))
        
        # Button colors
        palette.setColor(QPalette.ColorRole.Button, QColor(DarkTheme.SURFACE))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(DarkTheme.TEXT))
        
        # Selection colors
        palette.setColor(QPalette.ColorRole.Highlight, QColor(DarkTheme.ACCENT))
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
        
        # Link colors
        palette.setColor(QPalette.ColorRole.Link, QColor(DarkTheme.ACCENT))
        palette.setColor(QPalette.ColorRole.LinkVisited, QColor("#6a5acd"))
        
        # Tool tips
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(DarkTheme.SURFACE))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(DarkTheme.TEXT))
        
        # Apply palette
        app.setPalette(palette)
        
        # Apply custom stylesheet for finer control
        app.setStyleSheet(DarkTheme._get_stylesheet())
    
    @staticmethod
    def _get_stylesheet() -> str:
        """Get the custom stylesheet for the dark theme."""
        return f"""
        /* General widget styling */
        QWidget {{
            font-family: "Segoe UI", Arial, sans-serif;
            font-size: 10pt;
        }}
        
        /* Menu bar */
        QMenuBar {{
            background-color: {DarkTheme.SURFACE};
            border-bottom: 1px solid {DarkTheme.BORDER};
        }}
        
        QMenuBar::item {{
            padding: 4px 8px;
            background-color: transparent;
        }}
        
        QMenuBar::item:selected {{
            background-color: {DarkTheme.HOVER};
        }}
        
        QMenuBar::item:pressed {{
            background-color: {DarkTheme.PRESSED};
        }}
        
        /* Menus */
        QMenu {{
            background-color: {DarkTheme.SURFACE};
            border: 1px solid {DarkTheme.BORDER};
        }}
        
        QMenu::item {{
            padding: 6px 20px;
        }}
        
        QMenu::item:selected {{
            background-color: {DarkTheme.ACCENT};
        }}
        
        QMenu::separator {{
            height: 1px;
            background-color: {DarkTheme.BORDER};
            margin: 4px 10px;
        }}
        
        /* Push buttons */
        QPushButton {{
            background-color: {DarkTheme.SURFACE};
            border: 1px solid {DarkTheme.BORDER};
            padding: 6px 16px;
            border-radius: 4px;
            min-width: 80px;
        }}
        
        QPushButton:hover {{
            background-color: {DarkTheme.HOVER};
            border-color: {DarkTheme.ACCENT};
        }}
        
        QPushButton:pressed {{
            background-color: {DarkTheme.PRESSED};
        }}
        
        QPushButton:disabled {{
            background-color: {DarkTheme.BACKGROUND};
            color: {DarkTheme.DISABLED};
            border-color: {DarkTheme.DISABLED};
        }}
        
        /* Line edits */
        QLineEdit {{
            background-color: {DarkTheme.SURFACE};
            border: 1px solid {DarkTheme.BORDER};
            padding: 6px;
            border-radius: 4px;
        }}
        
        QLineEdit:focus {{
            border-color: {DarkTheme.ACCENT};
        }}
        
        QLineEdit:disabled {{
            background-color: {DarkTheme.BACKGROUND};
            color: {DarkTheme.DISABLED};
        }}
        
        /* Combo boxes */
        QComboBox {{
            background-color: {DarkTheme.SURFACE};
            border: 1px solid {DarkTheme.BORDER};
            padding: 6px;
            border-radius: 4px;
            min-width: 120px;
        }}
        
        QComboBox:hover {{
            border-color: {DarkTheme.ACCENT};
        }}
        
        QComboBox:disabled {{
            background-color: {DarkTheme.BACKGROUND};
            color: {DarkTheme.DISABLED};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid {DarkTheme.TEXT};
            margin-right: 8px;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {DarkTheme.SURFACE};
            border: 1px solid {DarkTheme.BORDER};
            selection-background-color: {DarkTheme.ACCENT};
        }}
        
        /* Labels */
        QLabel {{
            color: {DarkTheme.TEXT};
        }}
        
        QLabel:disabled {{
            color: {DarkTheme.DISABLED};
        }}
        
        /* Status bar */
        QStatusBar {{
            background-color: {DarkTheme.SURFACE};
            border-top: 1px solid {DarkTheme.BORDER};
        }}
        
        /* Scroll bars */
        QScrollBar:vertical {{
            background-color: {DarkTheme.BACKGROUND};
            width: 12px;
            border: none;
        }}
        
        QScrollBar:horizontal {{
            background-color: {DarkTheme.BACKGROUND};
            height: 12px;
            border: none;
        }}
        
        QScrollBar::handle:vertical,
        QScrollBar::handle:horizontal {{
            background-color: {DarkTheme.BORDER};
            border-radius: 6px;
            min-height: 20px;
            min-width: 20px;
        }}
        
        QScrollBar::handle:vertical:hover,
        QScrollBar::handle:horizontal:hover {{
            background-color: {DarkTheme.HOVER};
        }}
        
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical,
        QScrollBar::add-line:horizontal,
        QScrollBar::sub-line:horizontal {{
            background: none;
            border: none;
        }}
        
        /* Tool tips */
        QToolTip {{
            background-color: {DarkTheme.SURFACE};
            color: {DarkTheme.TEXT};
            border: 1px solid {DarkTheme.BORDER};
            padding: 4px;
        }}
        
        /* Group boxes */
        QGroupBox {{
            border: 1px solid {DarkTheme.BORDER};
            border-radius: 4px;
            margin-top: 8px;
            padding-top: 8px;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 8px;
            padding: 0 4px;
            background-color: {DarkTheme.BACKGROUND};
        }}
        
        /* Progress bars */
        QProgressBar {{
            background-color: {DarkTheme.SURFACE};
            border: 1px solid {DarkTheme.BORDER};
            border-radius: 4px;
            text-align: center;
            height: 20px;
        }}
        
        QProgressBar::chunk {{
            background-color: {DarkTheme.ACCENT};
            border-radius: 3px;
        }}
        
        /* Tab widgets */
        QTabWidget::pane {{
            background-color: {DarkTheme.BACKGROUND};
            border: 1px solid {DarkTheme.BORDER};
        }}
        
        QTabBar::tab {{
            background-color: {DarkTheme.SURFACE};
            border: 1px solid {DarkTheme.BORDER};
            padding: 6px 12px;
            margin-right: 2px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {DarkTheme.BACKGROUND};
            border-bottom-color: {DarkTheme.BACKGROUND};
        }}
        
        QTabBar::tab:hover {{
            background-color: {DarkTheme.HOVER};
        }}
        
        /* Text edits */
        QTextEdit, QPlainTextEdit {{
            background-color: {DarkTheme.SURFACE};
            border: 1px solid {DarkTheme.BORDER};
            border-radius: 4px;
        }}
        
        QTextEdit:focus, QPlainTextEdit:focus {{
            border-color: {DarkTheme.ACCENT};
        }}
        """