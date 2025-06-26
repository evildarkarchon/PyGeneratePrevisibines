#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from PrevisLib import BuildMode, Settings, setup_logger
from PrevisLib.models.data_classes import BuildStep
from PrevisLib.utils.validation import validate_plugin_name

def test_foundation():
    print("Testing PyGeneratePrevisibines Foundation...")
    
    # Test logging
    logger = setup_logger(verbose=True)
    logger.info("Logger initialized successfully")
    
    # Test settings
    settings = Settings.from_cli_args(
        plugin_name="TestMod.esp",
        build_mode="clean",
        verbose=True
    )
    
    print(f"\nSettings created:")
    print(f"  Plugin: {settings.plugin_name}")
    print(f"  Build Mode: {settings.build_mode.value}")
    print(f"  Archive Tool: {settings.archive_tool.value}")
    
    # Test validation
    valid_names = ["MyMod.esp", "TestPlugin.esm", "Patch.esl"]
    invalid_names = ["My Mod.esp", "Fallout4.esm", ""]
    
    print("\nTesting plugin name validation:")
    for name in valid_names:
        is_valid, error = validate_plugin_name(name)
        print(f"  {name}: {'✓ Valid' if is_valid else f'✗ Invalid - {error}'}")
    
    for name in invalid_names:
        is_valid, error = validate_plugin_name(name)
        print(f"  {name}: {'✓ Valid' if is_valid else f'✗ Invalid - {error}'}")
    
    # Test build steps
    print("\nBuild Steps:")
    for step in BuildStep:
        print(f"  {step.value}. {step}")
    
    # Test tool paths
    print("\nTool Paths:")
    errors = settings.tool_paths.validate()
    if errors:
        for error in errors:
            print(f"  ✗ {error}")
    else:
        print("  ✓ All tools found")
    
    print("\nFoundation test complete!")


if __name__ == "__main__":
    test_foundation()