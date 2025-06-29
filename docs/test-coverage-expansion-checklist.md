# Test Coverage Expansion Checklist for 85% Coverage

## Current Status: 40% → Target: 85% Coverage

✅ Phase 1 Complete: Core Builder Logic (+15% coverage achieved)
🔄 Phase 4 Partial: Some mocking infrastructure in place  
❌ Phase 2 Pending: Tool Integration (biggest coverage gains available)
❌ Phase 3 Pending: Configuration & Platform-Specific  
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

- [ ] **Archive operations (`archive.py`)**:
  - [ ] Mock Archive2/BSArch tool execution
  - [ ] Test file list generation
  - [ ] Test archive creation/extraction
  - [ ] Test error handling for missing tools

- [ ] **CKPE configuration (`ckpe.py`)**:
  - [ ] Test TOML/INI parsing
  - [ ] Test config file generation
  - [ ] Test validation of CKPE settings
  - [ ] Test error handling for malformed configs

### Phase 3: Configuration & Platform-Specific (+10% coverage to 85%)

#### **Expand `test_config.py`**
- [ ] **Registry operations (`registry.py`)**:
  - [ ] Mock `winreg` module completely
  - [ ] Test Steam/GOG installation detection
  - [ ] Test Creation Kit path resolution
  - [ ] Test registry read failures
  - [ ] Test non-Windows platform handling

#### **New Test File: `test_settings.py`**
- [ ] Test `Settings` class validation
- [ ] Test CLI argument parsing edge cases
- [ ] Test configuration loading/saving
- [ ] Test invalid configuration handling
- [ ] Test default value fallbacks

#### **New Test File: `test_main_cli.py`**
- [ ] Test main CLI interface (`previs_builder.py`)
- [ ] Test interactive prompts and user input
- [ ] Test progress display functionality
- [ ] Test error reporting and logging
- [ ] Test command-line argument validation

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

1. **High Impact (Core functionality)**:
   - `test_builder.py` - Main orchestration logic
   - `test_build_steps.py` - Step implementations
   - Registry mocking in `test_config.py`

2. **Medium Impact (Tool integration)**:
   - xEdit automation tests
   - Archive operation tests
   - CKPE configuration tests

3. **Low Impact (CLI/UI)**:
   - Main CLI interface tests
   - Settings validation tests
   - Progress display tests

### Testing Commands to Verify Progress
```bash
poetry run pytest --cov --cov-report=term-missing  # Check current coverage
poetry run pytest --cov --cov-report=html         # Generate HTML report
poetry run pytest -k "test_builder"               # Run specific test groups
```

## Current Test Coverage Analysis

### Current Coverage Status (40%)
- **Total Coverage**: 39.70% (760/1329 lines missed)
- **Test Files**: 9 test files covering 139 test cases
- **Target**: 85% coverage required

### Current Test File Structure

The existing test files are:
- `test_cli.py` - Command line parsing (87 tests)
- `test_config.py` - Configuration management (7 tests)  
- `test_data_classes.py` - Data models (9 tests)
- `test_file_system.py` - File operations (13 tests)
- `test_file_system_extended.py` - Extended file operations (21 tests)
- `test_process.py` - Process execution (24 tests)
- `test_tools.py` - Tool wrappers (15 tests)
- `test_utils.py` - Utility functions (12 tests)
- `test_validation.py` - Validation logic (29 tests)

### Main Codebase Modules Needing Coverage

**Critical Low Coverage Modules (10-24% coverage):**
1. **`PrevisLib/core/builder.py`** (10% coverage) - Main orchestration logic
2. **`PrevisLib/core/build_steps.py`** (10% coverage) - Build step implementations
3. **`PrevisLib/tools/xedit.py`** (10% coverage) - xEdit automation
4. **`PrevisLib/tools/archive.py`** (11% coverage) - Archive operations
5. **`PrevisLib/tools/ckpe.py`** (16% coverage) - CKPE configuration handling
6. **`PrevisLib/config/registry.py`** (17% coverage) - Windows registry operations
7. **`previs_builder.py`** (24% coverage) - Main CLI entry point
8. **`PrevisLib/config/settings.py`** (33% coverage) - Settings management

**Well-Tested Modules (>84% coverage):**
- `PrevisLib/tools/creation_kit.py` (84%)
- `PrevisLib/utils/logging.py` (94%)
- `PrevisLib/models/data_classes.py` (95%)
- `PrevisLib/utils/file_system.py` (99%)
- `PrevisLib/utils/validation.py` (100%)

### Coverage Gaps Identified

#### 1. Core Builder Logic (PrevisLib/core/)
- **builder.py**: Missing tests for all build step methods, error handling, resume functionality
- **build_steps.py**: Missing tests for validation methods, file preparation, compatibility checks

#### 2. Tool Integration (PrevisLib/tools/)
- **xedit.py**: Missing tests for window automation, log parsing, error detection
- **archive.py**: Missing tests for Archive2/BSArch operations, file list handling
- **ckpe.py**: Missing tests for TOML/INI parsing, config generation

#### 3. Configuration Management (PrevisLib/config/)
- **registry.py**: Missing comprehensive Windows registry tests
- **settings.py**: Missing tests for validation, CLI args parsing

#### 4. Main Application Logic
- **previs_builder.py**: Missing tests for CLI interface, interactive prompts, progress display
- **PyGeneratePrevisibines.py**: Minimal wrapper, needs integration tests

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

## Recommendations for Expanding Test Coverage

### Phase 1: Core Builder Tests (Target: +15% coverage)
**New Test Files Needed:**
- `test_builder.py` - Test `PrevisBuilder` class
- `test_build_steps.py` - Test `BuildStepExecutor` class

**Key Test Areas:**
- Build process orchestration and step execution
- Error handling and recovery mechanisms
- Resume functionality from failed steps
- File validation and cleanup operations

### Phase 2: Tool Integration Tests (Target: +20% coverage)
**Expand Existing Files:**
- `test_tools.py` - Add comprehensive tool wrapper tests

**Key Test Areas:**
- xEdit automation with mocked `pywinauto`
- Archive creation/extraction operations
- CKPE configuration parsing and generation
- Error detection in tool logs

### Phase 3: Configuration & CLI Tests (Target: +10% coverage)
**New Test Files:**
- `test_settings.py` - Test Settings class validation
- `test_main_cli.py` - Test main CLI interface

**Key Test Areas:**
- Settings validation and loading
- Interactive prompts and user input
- CLI argument parsing edge cases
- Progress display and error reporting

### Implementation Strategy

1. **Create Mock Infrastructure**:
   - Windows environment simulation
   - Tool execution mocking
   - File system fixtures

2. **Prioritize High-Impact Tests**:
   - Focus on core builder logic first
   - Add comprehensive error handling tests
   - Test platform-specific code paths

3. **Incremental Coverage Goals**:
   - Phase 1: 40% → 55%
   - Phase 2: 55% → 75% 
   - Phase 3: 75% → 85%

This checklist prioritizes the modules with lowest current coverage that have the highest impact on overall functionality, focusing on core builder logic first, then tool integration, and finally CLI/configuration components.