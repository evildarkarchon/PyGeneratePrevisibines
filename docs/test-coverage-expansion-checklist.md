# Test Coverage Expansion Checklist for 85% Coverage

## Current Status: 78% → Target: 85% Coverage

✅ Phase 1 Complete: Core Builder Logic
✅ Phase 2 Complete: Tool Integration
✅ Phase 3 Complete: Configuration & Platform-Specific
🔄 Phase 4 Partial: Some mocking infrastructure in place
❌ Phase 5 Pending: Integration & Edge Cases

### Phase 1: Core Builder Logic (+15% coverage to 55%)

#### **New Test File: `test_builder.py`**
- [x] Test `PrevisBuilder` class initialization
- [x] Test build process orchestration for all 8 steps
- [x] Test resume functionality from failed steps
- [x] Test error handling and recovery mechanisms
- [x] Test file validation before/after each step
- [x] Test cleanup operations on failure
- [x] Test build mode selection (clean/filtered/xbox)
- [x] Mock tool execution for cross-platform testing

#### **New Test File: `test_build_steps.py`**
- [x] Test `BuildStepExecutor` class methods
- [x] Test step validation logic
- [x] Test file preparation operations
- [x] Test compatibility checks
- [x] Test step dependencies and ordering
- [x] Test step success/failure detection

### Phase 2: Tool Integration (+20% coverage to 75%)

#### **Expand `test_tools.py`**
- [ ] **xEdit automation (`xedit.py`)**:
  - [ ] Mock `pywinauto` window interactions
  - [ ] Test script execution and window control
  - [ ] Test log parsing for error detection
  - [ ] Test timeout handling
  - [ ] Test "OUT OF HANDLE ARRAY ENTRIES" detection

- [x] **Archive operations (`archive.py`)**:
  - [x] Mock Archive2/BSArch tool execution
  - [x] Test file list generation
  - [x] Test archive creation/extraction
  - [x] Test error handling for missing tools

- [x] **CKPE configuration (`ckpe.py`)**:
  - [x] Test TOML/INI parsing
  - [x] Test config file generation
  - [x] Test validation of CKPE settings
  - [x] Test error handling for malformed configs

### Phase 3: Configuration & Platform-Specific (+10% coverage to 85%)

#### **Expand `test_config.py`**
- [x] **Registry operations (`registry.py`)**:
  - [x] Mock `winreg` module completely
  - [x] Test Steam/GOG installation detection
  - [x] Test Creation Kit path resolution
  - [x] Test registry read failures
  - [x] Test non-Windows platform handling

#### **New Test File: `test_settings.py`**
- [ ] Test `Settings` class validation
- [ ] Test CLI argument parsing edge cases
- [ ] Test configuration loading/saving
- [ ] Test invalid configuration handling
- [ ] Test default value fallbacks

#### **New Test File: `test_main_cli.py`**
- [x] Test main CLI interface (`previs_builder.py`)
- [x] Test interactive prompts and user input
- [x] Test progress display functionality
- [x] Test error reporting and logging
- [x] Test command-line argument validation

### Phase 4: Platform-Specific Mocking Infrastructure

#### **Cross-Platform Testing Setup**
- [ ] Create `conftest.py` fixtures for Windows simulation
- [ ] Mock `sys.platform` detection
- [ ] Create Windows path fixtures (`C:\Program Files\...`)
- [ ] Mock `subprocess` for tool execution
- [ ] Create sample tool output files for testing

#### **Windows-Only Module Mocking**
- [ ] Complete `winreg` module mocking
- [ ] Complete `pywinauto` module mocking
- [ ] Mock Windows-specific file operations
- [ ] Test fallback behavior on non-Windows platforms

### Phase 5: Integration & Edge Cases

#### **Integration Tests**
- [ ] Test complete build process end-to-end (mocked)
- [ ] Test error propagation through build steps
- [ ] Test file system state validation
- [ ] Test MO2 compatibility delays

#### **Error Handling & Edge Cases**
- [ ] Test missing tool executables
- [ ] Test corrupted configuration files
- [ ] Test insufficient disk space scenarios
- [ ] Test permission errors
- [ ] Test network/file system unavailability

### Implementation Priority Order

1. **High Impact (Final Push to 85%)**:
   - `test_main_cli.py` - Test `previs_builder.py` (64%) and `PyGeneratePrevisibines.py` (0%)
   - `test_settings.py` - Test `PrevisLib/config/settings.py` (66%)
   - Expand `test_builder.py` - Focus on error handling in `PrevisLib/core/builder.py` (67%)

2. **Medium Impact (Polish and Edge Cases)**:
   - Expand `test_tools.py` - Cover remaining `pywinauto` mocking for `xedit.py` (72%)
   - Expand `test_file_system.py` - Cover remaining branches (74%)

3. **Low Impact (Clean-up)**:
   - Final review of any remaining low-coverage lines.

### Testing Commands to Verify Progress
```bash
poetry run pytest --cov --cov-report=term-missing  # Check current coverage
poetry run pytest --cov --cov-report=html         # Generate HTML report
poetry run pytest -k "test_builder"               # Run specific test groups
```

## Current Test Coverage Analysis

### Current Coverage Status (77%)
- **Total Coverage**: 77%
- **Target**: 85% coverage required

### Main Codebase Modules Needing Coverage

**Modules to Target for 85% Goal (<80% coverage):**
1. **`PyGeneratePrevisibines.py`** (0% coverage) - Main entry point
2. **`previs_builder.py`** (64% coverage) - Main CLI application
3. **`PrevisLib/config/settings.py`** (66% coverage) - Settings management
4. **`PrevisLib/core/builder.py`** (67% coverage) - Core orchestration logic
5. **`PrevisLib/tools/xedit.py`** (72% coverage) - xEdit automation
6. **`PrevisLib/utils/file_system.py`** (74% coverage) - File system utilities

**High Coverage Modules (>80% coverage):**
- `PrevisLib/utils/process.py` (80%)
- `PrevisLib/core/build_steps.py` (80%)
- `PrevisLib/utils/validation.py` (81%)
- `PrevisLib/tools/creation_kit.py` (83%)
- `PrevisLib/config/registry.py` (92%)
- `PrevisLib/utils/logging.py` (94%)
- `PrevisLib/tools/archive.py` (95%)
- `PrevisLib/models/data_classes.py` (96%)
- `PrevisLib/tools/ckpe.py` (100%)

### Coverage Gaps Identified

#### 1. Main Application & CLI
- **`previs_builder.py` / `PyGeneratePrevisibines.py`**: The highest priority. Needs integration tests for argument parsing, user interaction, and various build modes.

#### 2. Configuration Management
- **`settings.py`**: Key logic for settings validation, loading, and default fallbacks remains untested.

#### 3. Core Builder & Tooling
- **`builder.py`**: Error handling, recovery paths, and specific command execution methods are not fully covered.
- **`xedit.py`**: Window automation logic (`pywinauto`) and log parsing still have significant gaps.

### Platform-Specific Testing Challenges

#### Windows-Only Functionality
1. **Registry Operations** (`registry.py`):
   - Uses `winreg` module only available on Windows
   - Current tests mock platform detection but don't test actual registry logic
   - Need comprehensive mocking of `winreg` operations

2. **Window Automation** (`xedit.py`):
   - Uses `pywinauto` for xEdit window control
   - Current tests have basic import mocking
   - Need detailed mocking of window interactions

3. **Tool Execution**:
   - Creation Kit, xEdit, Archive tools are Windows-only
   - Process execution needs mocking for cross-platform testing

#### Testing Strategy for Windows-Only Code
- Mock `sys.platform` to simulate Windows environment
- Mock `winreg` module for registry operations
- Mock `subprocess` and `pywinauto` for tool execution
- Create fixtures for common Windows paths and registry structures

## Recommendations for Final Push to 85%

### Priority 1: Main Application & Configuration Tests
**New or Expanded Test Files:**
- `test_main_cli.py` - Test `previs_builder.py` CLI and application flow.
- `test_settings.py` - Test `Settings` class validation and configuration loading.

**Key Test Areas:**
- Full end-to-end runs with mocked tools.
- CLI argument parsing (`--clean`, `--filter`, etc.).
- Settings validation, loading from files, and default value handling.

### Priority 2: Core Logic and Tooling Polish
**Expand Existing Files:**
- `test_builder.py` - Focus on error and recovery paths.
- `test_tools.py` - Mock `pywinauto` to test `xedit.py` window control.

**Key Test Areas:**
- Test specific build step failures and the resume process.
- Mock xEdit window interactions and test log parsing for error detection.

### Priority 3: Fill Remaining Gaps
**Focus on files just under the wire:**
- `test_file_system.py` - Add tests for remaining conditional branches.
- `test_process.py` - Cover the last few untested lines in process execution.

### Implementation Strategy

1. **Prioritize High-Impact CLI Tests**:
   - Start with `test_main_cli.py` as it will cover the most ground and touch many parts of the application.

2. **Complete Configuration Tests**:
   - Build out `test_settings.py` to ensure all configuration paths are stable.

3. **Incremental Coverage Gains**:
   - Target remaining functions and branches in `builder.py`, `xedit.py`, and `file_system.py` to push the total coverage over the 85% goal.

This checklist prioritizes the modules with lowest current coverage that have the highest impact on overall functionality, focusing on core builder logic first, then tool integration, and finally CLI/configuration components.