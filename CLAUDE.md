# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PyGeneratePrevisibines is a Python port of PJM's GeneratePrevisibines.bat (V2.9) for Fallout 4. It automates the generation of precombined meshes and visibility data (previsibines) for Fallout 4 mods to improve game performance.

## Development Commands

### Setup
```bash
poetry install                    # Install core dependencies
poetry install --with win32      # Install with Windows-specific dependencies
```

### Development
```bash
poetry run pytest                # Run all tests
poetry run pytest -k test_name   # Run specific test
poetry run black .               # Format code
poetry run ruff check .          # Lint code
poetry run ruff check --fix .    # Auto-fix linting issues
poetry run mypy .                # Type check
poetry run pytest --cov          # Run tests with coverage
```

### Running the Application
```bash
poetry run python PyGeneratePrevisibines.py [options]
# Options: [-clean|-filtered|-xbox] [-bsarch] [modname.esp]
```

## Architecture

The project follows a modular architecture as outlined in `previs-builder-checklist.md`:

### Core Package Structure
- **PrevisLib/config/**: Configuration management, registry reading, CKPE config parsing
- **PrevisLib/core/**: Main builder orchestration, build modes, and step implementations
- **PrevisLib/tools/**: Wrappers for Creation Kit, xEdit/FO4Edit, and Archive tools
- **PrevisLib/utils/**: File operations, process execution, validation, and logging
- **PrevisLib/models/**: Data classes for configuration

### Build Process
The tool executes 8 distinct steps:
1. Generate precombined meshes (Creation Kit)
2. Merge combined objects (xEdit)
3. Archive meshes (Archive2/BSArch)
4. Compress PSG files (Creation Kit)
5. Build CDX files (Creation Kit)
6. Generate visibility data (Creation Kit)
7. Merge previs data (xEdit)
8. Final packaging

### Key Implementation Notes

1. **Windows Tool Integration**: The project wraps Windows-only tools (Creation Kit, xEdit, Archive2/BSArch) and must handle window automation for xEdit operations.

2. **MO2 Compatibility**: File operations must include proper delays to allow Mod Organizer 2's virtual file system to update.

3. **Error Detection**: Must parse Creation Kit and xEdit logs for specific error patterns like "OUT OF HANDLE ARRAY ENTRIES" and "visibility task did not complete".

4. **Build Modes**:
   - `clean`: Full rebuild
   - `filtered`: Selective generation
   - `xbox`: Optimized for Xbox

5. **Resume Functionality**: Support resuming from any failed step without repeating successful operations.

## Platform Limitations

When developing on Linux:
- Registry reading functionality cannot be tested
- Window automation (pywinauto) features cannot be tested
- Tool execution must be mocked for testing

## Code Style

- Use type hints throughout (Python 3.12+ syntax supported)
- Follow black formatting (140 char line length)
- Comprehensive ruff linting rules are enforced
- Minimum 85% test coverage required
- Use pathlib.Path for all file operations
- Prefer loguru for logging over standard logging

## Current Implementation Status

The project is in early development with:
- Empty main Python file (PyGeneratePrevisibines.py)
- Comprehensive implementation checklist available
- Original batch file included for reference
- All tooling and dependencies configured

Start implementation following the phases outlined in `previs-builder-checklist.md`, beginning with Phase 1 (Foundation).