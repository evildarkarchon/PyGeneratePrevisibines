# PyGeneratePrevisibines

Python port of PJM's GeneratePrevisibines batch file for Fallout 4.

## Features

- **Build Automation**: Automated generation of precombined meshes and previs data for Fallout 4 mods
- **Multiple Modes**: Clean, filtered, and xbox build modes
- **Tool Integration**: Seamless integration with Creation Kit, xEdit, and archive tools
- **Cross-Platform**: Designed to work on Windows with graceful fallbacks for other platforms
- **Comprehensive Testing**: Full test suite with 85% coverage target

## Status

🚧 **Under Development** - Phase 5 (Polish) In Progress

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
- ✅ Tool Integration (Creation Kit, xEdit, Archive tools)
- ✅ Build Logic implementation

### Current Focus - Phase 5: Polish
- Refining error messages and user experience
- Performance optimizations
- Documentation improvements
- Final testing and bug fixes

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/PyGeneratePrevisibines.git
cd PyGeneratePrevisibines
```

2. Install dependencies using Poetry:
```bash
# Install base dependencies
poetry install

# Install Windows-specific dependencies (required for full functionality)
poetry install --with win32
```

## Usage

Run the tool using Poetry:

```bash
poetry run python previs_builder.py <plugin_name> [options]
```

### Available Options:
- `--clean`: Use clean build mode (default)
- `--filtered`: Use filtered build mode  
- `--xbox`: Use xbox build mode
- `--bsarch`: Use BSArch instead of Archive2
- `--verbose`: Enable verbose logging

### Example:
```bash
poetry run python previs_builder.py MyMod.esp --clean --verbose
```

## Testing

### Running Tests

**Important**: Always run tests using Poetry to ensure the correct virtual environment:

```bash
# Run all tests
poetry run pytest

# Run tests with coverage report
poetry run pytest --cov

# Run specific test file
poetry run pytest tests/test_config.py -v

# Run tests and stop on first failure
poetry run pytest -x

# Generate HTML coverage report
poetry run pytest --cov --cov-report=html
```

### Current Test Status
- **224 test cases** across 11 test modules
- **Target coverage goal**: 85%
- **Current coverage**: ~85%

### Test Coverage Goals
The project follows a comprehensive testing strategy:
- Unit tests for all core functionality
- Integration tests for tool wrappers
- Platform-specific mocking for Windows-only features
- Comprehensive error handling tests

## Development

This project uses modern Python development practices:
- **Type annotations** (Python 3.12 style with `|` unions)
- **Poetry** for dependency management
- **pytest** for testing with coverage reporting
- **mypy** for static type checking
- **ruff** for linting and formatting

### Code Quality Standards
- Minimum 85% test coverage required
- All new functions must have corresponding unit tests
- Use specific exception handling (avoid bare `except:`)
- Follow established module structure in `PrevisLib/`

## Project Structure

```
PyGeneratePrevisibines/
├── PrevisLib/           # Main library code
│   ├── core/           # Core builder logic
│   ├── config/         # Configuration management
│   ├── models/         # Data classes and models
│   ├── tools/          # Tool integrations (Creation Kit, xEdit, etc.)
│   └── utils/          # Utility functions
├── tests/              # Comprehensive test suite
├── previs_builder.py   # Main CLI entry point
└── pyproject.toml      # Project configuration
```

## Contributing

1. Ensure all tests pass: `poetry run pytest`
2. Maintain test coverage above 85%
3. Add tests for any new functionality
4. Follow the existing code style and structure
5. Use type annotations for all new code

## Requirements

- Python 3.12 or later
- Windows OS (for Creation Kit and tool integrations)
- [Poetry](https://python-poetry.org/) for dependency management

## License

GNU GPL Version 3.0 - see [LICENSE](LICENSE) file for details.
