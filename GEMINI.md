
## Project Overview
PyGeneratePrevisibines is a Python port of PJM's GeneratePrevisibines batch file for Fallout 4. It automates the generation of precombined meshes and previs data for Fallout 4 mods, which are essential for game performance optimization.

## Common Development Commands

### Running the Application
```bash
# Run CLI version
poetry run python previs_builder.py <plugin_name> [options]

# Run GUI version (in development)
poetry run python previs_gui.py
```

### Testing Commands
```bash
# Run all tests with coverage
poetry run pytest --cov

# Run specific test file
poetry run pytest tests/test_config.py -v

# Run single test
poetry run pytest tests/test_config.py::TestConfigManager::test_load_config -v

# Generate HTML coverage report
poetry run pytest --cov --cov-report=html

# Stop on first failure
poetry run pytest -x
```

### Code Quality Commands
```bash
# Type checking
poetry run mypy .

# Linting
poetry run ruff check .

# Auto-fix linting issues
poetry run ruff check --fix .

# Code formatting
poetry run black .

# Check formatting without changing files
poetry run black --check .
```

## High-Level Architecture

### Build Pipeline
The tool executes an 8-step pipeline to generate precombined meshes and previs data:

1. **GENERATE_PRECOMBINED**: Creates precombined meshes using Creation Kit
2. **MERGE_COMBINED_OBJECTS**: Merges CombinedObjects.esp into main plugin using xEdit
3. **ARCHIVE_MESHES**: Packages meshes into .ba2 archive using Archive2/BSArch
4. **COMPRESS_PSG**: Compresses PSG files (Clean mode only)
5. **BUILD_CDX**: Builds CDX index file (Clean mode only)
6. **GENERATE_PREVIS**: Generates previs data using Creation Kit
7. **MERGE_PREVIS**: Merges Previs.esp into main plugin using xEdit
8. **FINAL_PACKAGING**: Creates final archives and performs cleanup

### Core Components

**PrevisLib/core/builder.py**: Main orchestrator that manages the entire build process
- Handles state management and step execution
- Implements build modes (Clean, Filtered, Xbox)
- Manages tool integration and error handling

**PrevisLib/config/**: Configuration management
- `settings.py`: Manages user settings and paths
- `registry.py`: Reads tool paths from Windows registry

**PrevisLib/tools/**: Tool wrappers
- `creation_kit.py`: Creation Kit automation
- `xedit.py`: xEdit/FO4Edit integration
- `archive_tools.py`: Archive2/BSArch integration
- `ckpe.py`: CKPE Configuration

**PrevisLib/models/**: Data structures
- `data_classes.py`: Core data models (BuildMode, BuildStep, ProcessResult) and Enums (BuildStatus, BuildMode)

## Development Standards (from copilot-instructions.md)

### Type Annotations
- **MANDATORY**: Use Python 3.12-style type annotations
- Use `|` union syntax (e.g., `str | None`)
- Import type hints under `TYPE_CHECKING` to avoid circular imports

### Test Synchronization (TOP PRIORITY)
- Every new function/method MUST have corresponding unit tests
- Test files should mirror source structure in `tests/`
- Minimum 85% test coverage requirement
- Update tests immediately when modifying code

### Exception Handling
- Be specific with exception types
- Avoid bare `except:` clauses
- Always log exception details
- Use context managers for resource management

### Platform Considerations
- Windows-focused tool for Fallout 4 modding
- Handle platform-specific code gracefully
- Provide meaningful error messages on non-Windows platforms

## GUI Development Status
The project is implementing a PyQt6 GUI (currently Phase 3/7 complete):
- Main window with dark theme
- Plugin input validation
- Build controls and mode selection
- Progress display with step tracking
- Log output viewer (in progress)

Entry point: `previs_gui.py` (GUI version), `previs_builder.py` (CLI version)
GUI modules: `PrevisLib/gui/`

## Important Notes
- Always run commands through Poetry to ensure correct virtual environment
- Test synchronization is TOP PRIORITY - no code without tests
- The tool requires specific Fallout 4 modding tools to be installed
- Registry access is used on Windows to find tool installations