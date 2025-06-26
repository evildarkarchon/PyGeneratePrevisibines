# PrevisBuilder Python Port Implementation Checklist

## Project Structure
```
PrevisBuilder/
├── previs_builder.py          # Main entry point
├── PrevisLib/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py        # Configuration classes
│   │   └── registry.py        # Registry access utilities
│   ├── core/
│   │   ├── __init__.py
│   │   ├── builder.py         # Main builder orchestration
│   │   ├── build_modes.py     # Build mode enum and logic
│   │   └── build_steps.py     # Individual build step implementations
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── creation_kit.py    # CK wrapper
│   │   ├── xedit.py          # xEdit/FO4Edit wrapper
│   │   ├── archive.py        # Archive2/BSArch wrapper
│   │   └── ckpe.py          # CKPE configuration handler
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── file_system.py    # File operations
│   │   ├── logging.py        # Logging utilities
│   │   ├── validation.py     # Path/file validation
│   │   └── process.py        # Process execution utilities
│   └── models/
│       ├── __init__.py
│       └── data_classes.py    # Data classes for configuration
```

## Core Components to Implement

### 1. **Configuration Management** (`PrevisLib/config/`)
- [x] Create `Settings` dataclass with all configuration options
- [x] Implement registry reader for finding tool paths (Testing not available on Linux)
- [x] Support for fallback/manual path configuration
- [x] Parse command line arguments (maintain compatibility with batch parameters)
- [x] Load and validate CKPE configuration (both .toml and .ini formats)

### 2. **Tool Wrappers** (`PrevisLib/tools/`)
- [ ] **CreationKit wrapper**:
  - [ ] `generate_precombined()` method
  - [ ] `compress_psg()` method
  - [ ] `build_cdx()` method
  - [ ] `generate_previs_data()` method
  - [ ] Error detection from CK log files
  
- [ ] **xEdit wrapper**:
  - [ ] `merge_combined_objects()` method
  - [ ] `merge_previs()` method
  - [ ] Script execution with proper window automation
  - [ ] Log parsing for error detection
  
- [ ] **Archive wrapper**:
  - [ ] Support both Archive2 and BSArch
  - [ ] `create_archive()` method
  - [ ] `extract_archive()` method
  - [ ] `add_to_archive()` method

### 3. **Build Process** (`PrevisLib/core/`)
- [ ] Implement `BuildMode` enum (clean, filtered, xbox)
- [ ] Create `BuildStep` enum for all 8 steps
- [ ] Implement `PrevisBuilder` class with:
  - [ ] Step execution logic
  - [ ] Resume from failed step functionality
  - [ ] Progress tracking
  - [ ] Error handling and recovery

### 4. **Utilities** (`PrevisLib/utils/`)
- [x] **File System Operations**:
  - [x] Directory cleaning/creation
  - [x] File existence checks
  - [x] MO2-aware file operations (with delays)
  
- [x] **Process Execution**:
  - [x] Subprocess wrapper with logging
  - [x] Window automation for xEdit (using pywinauto or similar) (Testing not available on Linux)
  - [x] Exit code handling
  
- [x] **Validation**:
  - [x] Plugin name validation (no spaces, reserved names)
  - [x] Tool availability checks
  - [ ] Version checking for tools
  
- [x] **Logging**:
  - [x] Unified logging system
  - [x] Log file creation and management
  - [x] Console output formatting

### 5. **Main Application** (`previs_builder.py`)
- [ ] Command line interface matching batch file parameters
- [ ] Interactive prompts for plugin selection
- [ ] Build mode selection UI
- [ ] Step selection for resume functionality
- [ ] Cleanup operations
- [ ] Final output summary

## Additional Python Dependencies

```toml
[project]
dependencies = [
    # Core utilities
    "click>=8.0",              # CLI framework
    "colorama>=0.4",           # Cross-platform colored terminal text
    "rich>=13.0",              # Rich text and beautiful formatting
    
    # Windows-specific
    "pywin32>=300",            # Windows API access
    "pywinauto>=0.6",          # Window automation for xEdit
    
    # Configuration
    "tomli>=2.0",              # TOML parser for CKPE config
    "pydantic>=2.0",           # Data validation and settings
    
    # Path and file handling
    "pathlib2>=2.3",           # Enhanced path operations (if Python < 3.10)
    
    # Process management
    "psutil>=5.9",             # Process utilities
    
    # Logging
    "loguru>=0.7",             # Better logging
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",             # Testing
    "pytest-mock>=3.0",        # Mock fixtures
    "mypy>=1.0",               # Type checking
    "black>=23.0",             # Code formatting
    "ruff>=0.1",               # Linting
]
```

## Implementation Order

### Phase 1 - Foundation
- [x] Set up project structure
- [x] Implement configuration and registry reading
- [x] Create data models
- [x] Set up logging system

### Phase 2 - Tool Integration
- [ ] Implement process execution utilities
- [ ] Create tool wrappers (start with CK)
- [ ] Add xEdit automation
- [ ] Implement archive handling

### Phase 3 - Build Logic
- [ ] Implement individual build steps
- [ ] Create build orchestration
- [ ] Add error handling and recovery
- [ ] Implement resume functionality

### Phase 4 - User Interface
- [ ] Command line argument parsing
- [ ] Interactive prompts
- [ ] Progress display
- [ ] Final reporting

### Phase 5 - Polish
- [ ] Add comprehensive type hints
- [ ] Write unit tests
- [ ] Add documentation
- [ ] Performance optimization

## Key Considerations

1. **MO2 Compatibility**: Implement proper delays after file operations to allow MO2 virtualization
2. **Error Handling**: Replicate batch file's error detection patterns
3. **Logging**: Maintain compatibility with existing log formats
4. **Path Handling**: Use `pathlib.Path` throughout with proper Windows path handling
5. **Process Control**: Handle subprocess timeouts and window automation carefully
6. **Type Safety**: Use proper type annotations with `typing` module throughout

## Original Batch File Features to Preserve

### Command Line Arguments
- `-clean` / `-filtered` / `-xbox` - Build mode selection
- `-bsarch` - Use BSArch instead of Archive2
- `[modname.esp]` - Direct plugin specification

### Interactive Features
- Plugin name prompt with validation
- Rename xPrevisPatch.esp option
- Resume from failed step menu
- Cleanup confirmation

### Error Detection Patterns
- "OUT OF HANDLE ARRAY ENTRIES" in CK log
- "visibility task did not complete" in CK log
- Script completion messages in xEdit logs
- Archive creation verification

### File Operations
- Empty directory checks before operations
- MO2-aware file movement delays
- Temporary file cleanup
- Archive extraction and re-archiving

## Testing Strategy

### Unit Tests
- [ ] Configuration loading and validation
- [ ] Registry reading
- [ ] Path validation
- [ ] Plugin name validation

### Integration Tests
- [ ] Tool wrapper execution
- [ ] File operations with mock filesystem
- [ ] Process execution and error handling

### End-to-End Tests
- [ ] Full build process with test plugin
- [ ] Resume functionality
- [ ] Error recovery scenarios

## Documentation Requirements

### User Documentation
- [ ] README with installation instructions
- [ ] Command line usage guide
- [ ] Troubleshooting guide
- [ ] Migration guide from batch file

### Developer Documentation
- [ ] API documentation for all modules
- [ ] Architecture overview
- [ ] Contributing guidelines
- [ ] Plugin development guide