# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PyGeneratePrevisibines is a Python port of PJM's GeneratePrevisibines batch file for Fallout 4. It automates the generation of precombined meshes and visibility data (previsibines) for Fallout 4 mods to improve game performance.

**Status**: Phase 1 (Foundation) Complete - Currently under active development

## Essential Commands

### Development Environment
```bash
# Install dependencies
poetry install

# Install with Windows-specific features
poetry install --with win32
```

### Running the Application
```bash
# Basic usage
poetry run python PyGeneratePrevisibines.py

# With parameters
poetry run python PyGeneratePrevisibines.py MyMod.esp --build-mode clean --verbose

# Using BSArch instead of Archive2
poetry run python PyGeneratePrevisibines.py MyMod.esp --bsarch
```

### Testing and Quality Assurance
```bash
# Run tests with coverage
poetry run pytest

# Code formatting
poetry run black .

# Linting
poetry run ruff check .

# Type checking
poetry run mypy .
```

## Architecture Overview

### Core Structure
- **Entry Points**: `PyGeneratePrevisibines.py` (wrapper) and `previs_builder.py` (main CLI)
- **Core Logic**: `PrevisLib/core/` - Contains `PrevisBuilder` orchestrator and `BuildStepExecutor`
- **Tool Integration**: `PrevisLib/tools/` - Wrappers for Creation Kit, xEdit, Archive tools
- **Configuration**: `PrevisLib/config/` - Settings management and Windows registry reading
- **Data Models**: `PrevisLib/models/data_classes.py` - Pydantic models for all components
- **Utilities**: `PrevisLib/utils/` - File system, logging, process execution, validation

### Key Components
1. **PrevisBuilder** (`PrevisLib/core/builder.py`): Main orchestrator that coordinates the build process
2. **BuildStepExecutor** (`PrevisLib/core/build_steps.py`): Handles individual build step execution
3. **Tool Wrappers**: Creation Kit, xEdit, Archive tools integration
4. **Settings System**: Comprehensive configuration management with Windows registry support

### Build Process Flow
The application follows a structured build pipeline:
1. Configuration validation and tool path resolution
2. Plugin validation and dependency checking
3. Build step execution (clean, filtered, or xbox modes)
4. Tool orchestration (Creation Kit → xEdit → Archive tools)
5. Output validation and cleanup

## Development Standards (Critical)

### Test Synchronization (TOP PRIORITY)
- **Every new function/method MUST have corresponding unit tests**
- Minimum 85% test coverage requirement
- Test files mirror source structure in `tests/`
- Run coverage: `poetry run pytest --cov=PrevisLib --cov-report=html`

### Type Annotations (MANDATORY)
- Use Python 3.12-style type annotations
- Prefer union syntax with `|` over `Union`
- Use `from __future__ import annotations` for forward references
- Import type hints under `TYPE_CHECKING` to avoid circular imports

### Exception Handling
- Avoid blind exception catching
- Be specific with exception types (`FileNotFoundError`, `ValueError`, etc.)
- When catching broad exceptions, always log details
- Use context managers for resource management

### Platform Considerations
- Windows-focused tool with graceful cross-platform degradation
- Handle registry access and Windows-specific paths appropriately
- Provide meaningful error messages on non-Windows platforms

## File Organization Rules
- Business logic: `PrevisLib/core/`
- Utilities: `PrevisLib/utils/`
- Data models: `PrevisLib/models/`
- Tool integrations: `PrevisLib/tools/`
- Configuration: `PrevisLib/config/`
- Tests: `tests/` (mirror source structure)

## Requirements
- Python 3.12+
- Windows OS (for full functionality)
- Fallout 4 with Creation Kit
- xEdit/FO4Edit
- Archive2 or BSArch