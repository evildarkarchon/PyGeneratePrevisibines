# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PyGeneratePrevisibines is a Python port of PJM's GeneratePrevisibines batch file for Fallout 4. It automates the generation of precombined meshes and previs data for Fallout 4 mods, which are essential for game performance optimization.

## Development Commands

### Setup and Dependencies
```bash
# Install all dependencies (including dev tools)
poetry install

# Install with Windows-specific features
poetry install --with win32
```

### Running the Application
```bash
# Basic usage
poetry run python previs_builder.py MyMod.esp --clean

# Available modes:
# --clean     Full rebuild from scratch
# --filtered  Resume from filtered cells step
# --xbox      Optimized build for Xbox platform
```

### Testing
```bash
# Run all tests with coverage
poetry run pytest --cov --cov-report=lcov:lcov.info --cov-report=term

# Run specific test file
poetry run pytest tests/test_config.py -v

# Generate HTML coverage report
poetry run pytest --cov --cov-report=html
```

### Code Quality
```bash
# Format code (line-length: 140)
poetry run black .

# Lint code
poetry run ruff check .

# Type checking
poetry run mypy .
poetry run pyright
```

## Architecture Overview

The project is organized into a modular library structure under `PrevisLib/`:

- **`config/`**: Settings management and Windows registry access for tool discovery
- **`core/`**: Main builder orchestration and build step implementations
- **`models/`**: Data models (enums, dataclasses) for build modes and steps
- **`tools/`**: Wrappers for external tools (Creation Kit, xEdit, Archive2/BSArch)
- **`utils/`**: File operations, logging, process execution, and validation

The build pipeline consists of 8 sequential steps that generate precombined meshes, merge ESP files, create archives, and generate previs data.

## Critical Development Rules

1. **Type Annotations are MANDATORY** - Use Python 3.12 style with `|` unions
2. **85% Test Coverage Required** - Every function must have corresponding tests
3. **Test Synchronization is TOP PRIORITY** - Update tests immediately when modifying code
4. **Platform Handling** - This is Windows-focused; provide meaningful errors on other platforms
5. **Exception Handling** - Use specific exceptions, never bare `except:`
6. **Module Structure** - Follow established patterns in `PrevisLib/`

## Build Pipeline Steps

1. `GENERATE_PRECOMBINED` - Create precombined meshes using Creation Kit
2. `MERGE_COMBINED_OBJECTS` - Merge CombinedObjects.esp into main plugin
3. `ARCHIVE_MESHES` - Package meshes into .ba2 archive
4. `COMPRESS_PSG` - Compress PSG files
5. `BUILD_CDX` - Build CDX index file
6. `GENERATE_PREVIS` - Generate previs data using Creation Kit
7. `MERGE_PREVIS` - Merge Previs.esp into main plugin
8. `FINAL_PACKAGING` - Final archive creation and cleanup

## Tool Integration Notes

- The project integrates with Creation Kit, xEdit/FO4Edit, and Archive2/BSArch
- Tool paths are discovered via Windows registry or configuration files
- CKPE (Creation Kit Platform Extended) support is included
- MO2 (Mod Organizer 2) integration is supported