# Python Development Standards for PyGeneratePrevisibines

## Type Annotations
- **MANDATORY**: Use Python 3.12-style type annotations for all new code
- Use `from __future__ import annotations` for forward references
- Prefer union syntax with `|` over `Union` (e.g., `str | None` instead of `Union[str, None]`)
- Use `types.ModuleType` for module parameters (as seen in `PrevisLib/config/registry.py`)
- Annotate return types explicitly, including `None` when appropriate
- Use generic types properly: `list[str]`, `dict[str, Any]`, etc.
- Import type hints under `TYPE_CHECKING` when needed to avoid circular imports

## Test Synchronization (TOP PRIORITY)
- **Every new function/method MUST have corresponding unit tests**
- Test files should mirror the source structure in `tests/`
- When modifying existing code, update or add tests immediately
- Follow the existing test patterns seen in `tests/test_config.py`, `tests/test_tools.py`
- Use descriptive test method names that explain what is being tested
- Group related tests in test classes when appropriate

## Code Coverage Requirements
- **TARGET**: Minimum 85% test coverage across the entire codebase
- Run coverage reports regularly
- Focus on covering edge cases and error conditions
- Ensure all public APIs in `PrevisLib/` modules are tested
- Test both success and failure paths

## Exception Handling
- **AVOID blind exception catching** unless absolutely necessary
- Be specific with exception types: catch `FileNotFoundError`, `ValueError`, etc.
- When catching broad exceptions like `Exception`, always log the details
- Follow the pattern in `PrevisLib/config/registry.py`: catch specific exceptions like `(OSError, ValueError)`
- Use context managers (`with` statements) for resource management
- Always clean up resources in exception scenarios

## Code Organization and Structure
- Follow the established module structure in `PrevisLib/`
- Keep business logic in `core/`, utilities in `utils/`, data models in `models/`
- Tool integrations belong in `tools/` (like `PrevisLib/tools/xedit.py`, `PrevisLib/tools/creation_kit.py`)
- Configuration management in `config/` (see `PrevisLib/config/settings.py`)
- Use proper logging via `PrevisLib/utils/logging.py` utilities

## Testing Patterns
- Use pytest fixtures for common test setup
- Mock external dependencies (file system, registry, subprocess calls)
- Test data classes in `PrevisLib/models/data_classes.py` thoroughly
- Validate file system operations in `PrevisLib/utils/file_system.py`
- Test process execution in `PrevisLib/utils/process.py` with mocked subprocesses

## Quality Assurance
- All code must pass type checking with mypy
- Use descriptive variable names and function signatures
- Include docstrings for public APIs
- Validate inputs using utilities from `PrevisLib/utils/validation.py`
- Log important operations using the logger from `PrevisLib/utils/logging.py`

## Platform Considerations
- This is a Windows-focused tool for Fallout 4 modding
- Handle platform-specific code (like registry access) gracefully
- Provide meaningful error messages when running on non-Windows platforms
- Test both Windows and cross-platform scenarios where applicable

## File References
- Main entry point: `PyGeneratePrevisibines.py`
- Core builder logic: `PrevisLib/core/builder.py`
- Build steps: `PrevisLib/core/build_steps.py`
- Project configuration: `pyproject.toml`
- Test suite: `tests/`

Remember: **Test synchronization is the TOP PRIORITY** - no code changes should be committed without corresponding test updates.
