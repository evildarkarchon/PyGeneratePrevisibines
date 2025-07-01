# PyQt6 GUI Implementation Checklist for PyGeneratePrevisibines

## Phase 1: Project Setup & Infrastructure

### Dependencies & Configuration
- [x] Add PyQt6 to `pyproject.toml` dependencies
  ```toml
  [tool.poetry.dependencies]
  PyQt6 = ">=6.9.1"
  ```
- [x] Update poetry.lock with `poetry lock`
- [x] Install new dependencies with `poetry install`
- [x] Add GUI entry point to `pyproject.toml`
  ```toml
  [tool.poetry.scripts]
  previs-gui = "previs_gui:main"
  ```

### Directory Structure
- [x] Create `PrevisLib/gui/` directory
- [x] Create `PrevisLib/gui/__init__.py`
- [x] Create `PrevisLib/gui/widgets/` directory
- [x] Create `PrevisLib/gui/widgets/__init__.py`
- [x] Create `PrevisLib/gui/styles/` directory
- [x] Create `PrevisLib/gui/styles/__init__.py`
- [x] Create `previs_gui.py` in project root

## Phase 2: Core GUI Components

### Main Window (`PrevisLib/gui/main_window.py`)
- [x] Create `MainWindow` class inheriting from `QMainWindow`
- [x] Set window title and default size (800x600)
- [x] Create central widget and main layout
- [x] Implement menu bar with File and Settings menus
- [x] Add status bar for general messages
- [x] Implement window state persistence (size, position)

### Dark Theme (`PrevisLib/gui/styles/dark_theme.py`)
- [x] Create `DarkTheme` class with static methods
- [x] Define color palette constants
  - [x] Background: #1e1e1e
  - [x] Surface: #2d2d2d
  - [x] Text: #e0e0e0
  - [x] Accent: #007acc
  - [x] Success: #4caf50
  - [x] Error: #f44336
  - [x] Warning: #ff9800
- [x] Create `apply_theme()` method for QApplication
- [x] Style all standard Qt widgets
- [x] Force dark mode regardless of system settings

### Plugin Input Widget (`PrevisLib/gui/widgets/plugin_input.py`)
- [x] Create `PluginInputWidget` class inheriting from `QWidget`
- [x] Add QLineEdit for plugin name
- [x] Implement auto-extension logic (.esp appending)
- [x] Add validation indicator (QLabel with icon)
- [x] Connect to existing plugin validator
- [x] Emit signal when validation state changes
- [x] Check if plugin exists in game data directory
- [x] Style with proper margins and spacing

### Build Controls Widget (`PrevisLib/gui/widgets/build_controls.py`)
- [x] Create `BuildControlsWidget` class
- [x] Add build mode QComboBox (Clean/Filtered/Xbox)
- [x] Add build step QComboBox (all 8 steps, CompressPSG and BuildCDX are only available in Clean mode)
- [x] Implement step selector enable/disable logic
- [x] Add Start/Stop QPushButton
- [x] Implement button state management
- [x] Connect signals for user interactions
- [x] Add tooltips for each control

### Progress Display Widget (`PrevisLib/gui/widgets/progress_display.py`)
- [ ] Create `ProgressDisplayWidget` class
- [ ] Add current step label (large, prominent)
- [ ] Add step counter (e.g., "Step 3 of 8")
- [ ] Create step list with status icons
- [ ] Implement status icon updates (pending/running/success/failed)
- [ ] Add time elapsed display
- [ ] Include cancel confirmation dialog

## Phase 3: Settings & Configuration

### Settings Dialog (`PrevisLib/gui/settings_dialog.py`)
- [ ] Create `SettingsDialog` class inheriting from `QDialog`
- [ ] Add tool paths section
  - [ ] Game executable path input with browse button
  - [ ] xEdit executable path input with browse button
  - [ ] BSArch executable path input with browse button
  - [ ] Path validation indicators for each
- [ ] Add archive tool selection (QRadioButton group)
- [ ] Implement browse dialogs with appropriate filters
- [ ] Add OK/Cancel buttons
- [ ] Validate all paths before allowing OK
- [ ] Save settings to persistent storage

### BSArch CLI Enhancement
- [ ] Add `--bsarch-path` argument to CLI parser
- [ ] Update `Settings` class to accept BSArch path
- [ ] Modify `ToolPaths` validation logic
- [ ] Update registry discovery to respect manual BSArch path
- [ ] Add BSArch path to configuration file schema
- [ ] Write tests for new BSArch path functionality

## Phase 4: Build Process Integration

### Build Thread (`PrevisLib/gui/build_thread.py`)
- [ ] Create `BuildThread` class inheriting from `QThread`
- [ ] Define Qt signals for:
  - [ ] Step started
  - [ ] Step progress (for xEdit steps, if information is available, for example, a log file.)
  - [ ] Step completed
  - [ ] Build completed
  - [ ] Build failed
  - [ ] Log message
- [ ] Implement run() method to execute PrevisBuilder
- [ ] Add cancellation support with proper cleanup
- [ ] Handle exceptions and emit error signals

### Progress Callback System
- [ ] Modify `PrevisBuilder` to accept progress callback
- [ ] Add callback invocations in each build step method
- [ ] Create callback data structure with:
  - [ ] Current step
  - [ ] Step status
  - [ ] Progress message
  - [ ] Timestamp
- [ ] Ensure thread-safe callback execution

### Build State Management
- [ ] Track current build state in MainWindow
- [ ] Implement UI updates based on build state
- [ ] Disable controls during build
- [ ] Enable stop button during build
- [ ] Show completion dialog on success
- [ ] Show error dialog on failure with details

## Phase 5: Advanced Features

### Log Viewer
- [ ] Create collapsible log panel
- [ ] Implement log level filtering (DEBUG/INFO/WARNING/ERROR)
- [ ] Add log search functionality
- [ ] Include timestamp display
- [ ] Add copy-to-clipboard for log entries
- [ ] Implement log auto-scroll with toggle

### State Persistence
- [ ] Create settings file in user config directory
- [ ] Save/load window geometry
- [ ] Save/load tool paths
- [ ] Save/load last used plugin name
- [ ] Save/load archive tool preference
- [ ] Save/load log viewer preferences

### Error Handling
- [ ] Create custom exception dialog
- [ ] Include stack trace in debug mode
- [ ] Add "Report Issue" button with GitHub link
- [ ] Implement recovery suggestions
- [ ] Log all errors to file

## Phase 6: Testing & Polish

### Unit Tests
- [ ] Test plugin name normalization
- [ ] Test validation logic
- [ ] Test settings persistence
- [ ] Test build thread signals
- [ ] Test cancellation handling
- [ ] Test error scenarios

### Integration Tests
- [ ] Test full build process via GUI
- [ ] Test settings dialog functionality
- [ ] Test build interruption
- [ ] Test invalid plugin handling
- [ ] Test missing tool handling

### UI Polish
- [ ] Add application icon
- [ ] Create custom icons for build steps
- [ ] Add keyboard shortcuts
- [ ] Implement drag-and-drop for plugin files
- [ ] Add "Recent Plugins" menu
- [ ] Create about dialog

### Documentation
- [ ] Update README with GUI instructions
- [ ] Create GUI user guide
- [ ] Document keyboard shortcuts
- [ ] Add screenshots to documentation
- [ ] Update CLAUDE.md with GUI architecture

## Phase 7: Packaging & Distribution

### PyInstaller Setup
- [ ] Create PyInstaller spec file
- [ ] Include all Qt dependencies
- [ ] Bundle dark theme resources
- [ ] Test on clean Windows system
- [ ] Create installer with NSIS/Inno Setup

### Release Preparation
- [ ] Version bump in pyproject.toml
- [ ] Update changelog
- [ ] Create GitHub release
- [ ] Upload compiled executables
- [ ] Update installation instructions

## Implementation Order

1. **Week 1**: Phase 1 & 2 (Setup and Core Components)
2. **Week 2**: Phase 3 (Settings and Configuration)
3. **Week 3**: Phase 4 (Build Process Integration)
4. **Week 4**: Phase 5 (Advanced Features)
5. **Week 5**: Phase 6 (Testing and Polish)
6. **Week 6**: Phase 7 (Packaging and Distribution)

## Notes

- Prioritize core functionality over advanced features
- Ensure CLI remains fully functional throughout development
- Test on multiple Windows versions (10, 11)
- Consider accessibility features (screen readers, high contrast)
- Keep GUI responsive during long operations
- Maintain consistent error handling patterns