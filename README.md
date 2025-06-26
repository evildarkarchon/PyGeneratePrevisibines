# PyGeneratePrevisibines

Python port of PJM's GeneratePrevisibines batch file for Fallout 4.

## Overview

PyGeneratePrevisibines automates the generation of precombined meshes and visibility data (previsibines) for Fallout 4 mods. This optimization technique significantly improves game performance by reducing draw calls.

## Status

🚧 **Under Development** - Phase 1 (Foundation) Complete

### Completed
- ✅ Project structure setup
- ✅ Configuration management system
- ✅ Data models for all components
- ✅ Logging system (using loguru)
- ✅ Registry reading for tool paths (Windows)
- ✅ File system utilities with MO2 support
- ✅ Process execution utilities
- ✅ Validation utilities
- ✅ Basic CLI interface

### Next Steps
- Phase 2: Tool Integration (Creation Kit, xEdit, Archive tools)
- Phase 3: Build Logic
- Phase 4: User Interface
- Phase 5: Polish

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd PyGeneratePrevisibines

# Install dependencies using Poetry
poetry install

# For Windows-specific features
poetry install --with win32
```

## Usage

```bash
# Basic usage
poetry run python PyGeneratePrevisibines.py

# With parameters
poetry run python PyGeneratePrevisibines.py MyMod.esp --build-mode clean --verbose

# Using BSArch instead of Archive2
poetry run python PyGeneratePrevisibines.py MyMod.esp --bsarch

# Test the foundation
poetry run python test_foundation.py
```

### Command Line Options
- `plugin_name`: The plugin to generate previsibines for
- `--build-mode`: Build mode (clean, filtered, xbox) - default: clean
- `--bsarch`: Use BSArch instead of Archive2
- `--verbose`: Enable verbose logging
- `--no-prompt`: Skip interactive prompts

## Development

### Running Tests
```bash
poetry run pytest
```

### Code Quality
```bash
poetry run black .          # Format code
poetry run ruff check .     # Lint code
poetry run mypy .           # Type check
```

## Requirements

- Python 3.12+
- Windows OS (for full functionality)
- Fallout 4 with Creation Kit
- xEdit/FO4Edit
- Archive2 or BSArch

## License

GNU GPL Version 3.0