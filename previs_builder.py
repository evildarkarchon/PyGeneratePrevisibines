#!/usr/bin/env python3
"""Main entry point for PyGeneratePrevisibines."""

from __future__ import annotations

import platform
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import click
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskID, TextColumn
from rich.prompt import Confirm, Prompt
from rich.table import Table

from PrevisLib.config.settings import Settings
from PrevisLib.core import PrevisBuilder
from PrevisLib.models.data_classes import BuildMode, BuildStep
from PrevisLib.utils.logging import get_logger, setup_logger
from PrevisLib.utils.validation import check_tool_version, create_plugin_from_template, validate_plugin_name

if TYPE_CHECKING:
    from loguru import Logger

console: Console = Console()
logger: Logger = get_logger(__name__)

# Banner art
BANNER = """
╔═══════════════════════════════════════════════════════════╗
║        Automatic Previsbine Builder for Fallout 4         ║
║                   Python Port v1.0.0                      ║
║              Based on GeneratePrevisibines.bat            ║
╚═══════════════════════════════════════════════════════════╝
"""



def prompt_for_plugin(settings: Settings | None = None) -> str:
    """Prompt user for plugin name with validation and template creation.

    Args:
        settings: Optional settings object with tool paths for template creation

    Returns:
        Valid plugin name

    Raises:
        KeyboardInterrupt: If user cancels with Ctrl+C
    """
    console.print("\n[cyan]Enter the plugin name for previs generation.[/cyan]")
    console.print("[dim]Example: MyMod.esp[/dim]")
    console.print("[dim]If the plugin doesn't exist, it will be created from xPrevisPatch.esp.[/dim]")
    console.print("[dim]Press Ctrl+C to exit.[/dim]")

    while True:
        plugin_name: str = Prompt.ask("\nPlugin name", default="")

        if not plugin_name.strip():
            console.print("[red]Plugin name cannot be empty. Please enter a valid plugin name.[/red]")
            continue

        # Validate plugin name
        validation_result: tuple[bool, str] = validate_plugin_name(plugin_name)
        is_valid, message = validation_result
        if not is_valid:
            console.print(f"\n[red]Error:[/red] {message}")
            continue

        # Check for reserved names that should be blocked
        reserved_build_names = {"previs", "combinedobjects", "xprevispatch"}
        plugin_base = Path(plugin_name).stem.lower()
        if plugin_base in reserved_build_names:
            console.print(f"\n[red]Error:[/red] Plugin name '{plugin_base}' is reserved for internal use. Please choose another.")
            continue

        # Check if plugin exists (if we have tool paths available)
        if settings and settings.tool_paths.fallout4:
            data_path = settings.tool_paths.fallout4 / "Data"
            plugin_path = data_path / plugin_name

            if not plugin_path.exists():
                # Plugin doesn't exist - offer to create from template
                console.print(f"\n[yellow]Plugin {plugin_name} does not exist.[/yellow]")

                if Confirm.ask("Create it from xPrevisPatch.esp?", default=True):
                    success, template_message = create_plugin_from_template(data_path, plugin_name)

                    if success:
                        console.print(f"\n[green]✓[/green] {template_message}")
                        return plugin_name
                    console.print(f"\n[red]Error:[/red] {template_message}")
                    continue
                # User declined to create template, ask for different name
                console.print("[dim]Please enter a different plugin name or create the plugin manually.[/dim]")
                continue

        return plugin_name


def prompt_for_build_mode() -> BuildMode:
    """Prompt user to select build mode.

    Returns:
        Selected build mode
    """
    console.print("\n[cyan]Select build mode:[/cyan]")

    modes: list[tuple[str, str, str, BuildMode]] = [
        ("1", "Clean", "Full rebuild - deletes existing previs data", BuildMode.CLEAN),
        ("2", "Filtered", "Only generate for filtered cells", BuildMode.FILTERED),
        ("3", "Xbox", "Optimized for Xbox platform", BuildMode.XBOX),
    ]

    table = Table(show_header=False, box=None)
    for num, name, desc, _ in modes:
        table.add_row(f"[cyan]{num}[/cyan]", f"[bold]{name}[/bold]", f"[dim]{desc}[/dim]")

    console.print(table)

    while True:
        choice: str = Prompt.ask("\nSelect mode", choices=["1", "2", "3"], default="1")

        for num, _, _, mode in modes:
            if choice == num:
                return mode


def prompt_for_resume(builder: PrevisBuilder) -> BuildStep | None:
    """Prompt user to select step to resume from.

    Args:
        builder: PrevisBuilder instance with resume options

    Returns:
        Selected step or None to start fresh
    """
    resume_options: list[BuildStep] = builder.get_resume_options()

    console.print("\n[cyan]Previous build was interrupted. Resume from:[/cyan]")

    table = Table(show_header=False, box=None)
    table.add_row("[cyan]0[/cyan]", "[bold]Start Fresh[/bold]", "[dim]Begin from the first step[/dim]")

    for i, step in enumerate(resume_options, 1):
        table.add_row(f"[cyan]{i}[/cyan]", f"[bold]{step}[/bold]", "")

    console.print(table)

    choices: list[str] = ["0"] + [str(i) for i in range(1, len(resume_options) + 1)]
    choice: str = Prompt.ask("\nSelect option", choices=choices, default="0")

    if choice == "0":
        return None
    return resume_options[int(choice) - 1]


def show_tool_versions(settings: Settings) -> None:
    """Display tool versions like the original batch file.

    Args:
        settings: Build settings containing tool paths
    """
    console.print("\n[bold cyan]Tool Versions:[/bold cyan]")

    tool_paths = settings.tool_paths

    # Helper function to display tool version
    def show_version(tool_name: str, tool_path: Path | None) -> None:
        if tool_path and tool_path.exists():
            success, version_info = check_tool_version(tool_path)
            if success:
                # Clean up version string - extract just the version number
                version: str = version_info.removeprefix("Version: ")
                console.print(f"Using {tool_name} V{version}")
            else:
                console.print(f"Using {tool_name} V[red]Unknown[/red] ({version_info})")
        else:
            console.print(f"Using {tool_name} V[red]Not Found[/red]")

    # Show tool versions in the same order as the batch file
    show_version(f"{(tool_paths.xedit.name if tool_paths.xedit else 'FO4Edit')}", tool_paths.xedit)
    show_version("Fallout4.exe", tool_paths.fallout4)
    show_version("CreationKit.exe", tool_paths.creation_kit)

    # Check for CKPE (winhttp.dll in FO4 directory)
    ckpe_dll_path = tool_paths.fallout4.parent / "winhttp.dll" if tool_paths.fallout4 else None
    show_version("CKPE", ckpe_dll_path)

    console.print()  # Add blank line after versions


def show_build_summary(settings: Settings) -> None:
    """Display build configuration summary.

    Args:
        settings: Build settings
    """
    console.print("\n[bold green]Build Configuration:[/bold green]")

    table = Table(show_header=False, box=None)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Plugin", settings.plugin_name)
    table.add_row("Build Mode", settings.build_mode.value.capitalize())
    table.add_row("Archive Tool", settings.archive_tool.value)

    if settings.ckpe_config:
        table.add_row("CKPE Config", "Loaded ✓")

    console.print(table)


def run_build(settings: Settings) -> bool | None:
    """Execute the build process.

    Args:
        settings: Build settings

    Returns:
        True if successful, False if failed, None if cancelled.
    """
    builder = PrevisBuilder(settings)

    # Check for previous failed build
    start_step: BuildStep | None = None
    if builder.failed_step:
        start_step = prompt_for_resume(builder)

    # Show summary
    show_build_summary(settings)

    if not Confirm.ask("\nProceed with build?", default=True):
        console.print("\n[yellow]Build cancelled.[/yellow]")
        return None

    # Run build with progress display
    console.print("\n[bold cyan]Starting build process...[/bold cyan]\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        # Create main task
        total_steps: int = len(list(BuildStep))
        task: TaskID = progress.add_task("Building previs...", total=total_steps)

        # Custom progress callback
        def update_progress(step: BuildStep, completed: bool) -> None:
            if completed:
                progress.update(task, advance=1)
                progress.update(task, description=f"Completed: {step}")
            else:
                progress.update(task, description=f"Running: {step}")

        # Inject progress callback (this would need to be added to builder)
        # For now, we'll simulate
        success: bool = builder.build(start_from_step=start_step)

    if success:
        console.print("\n[bold green]✓ Build completed successfully![/bold green]")

        # Show output files (corrected to match actual output)
        plugin_base: str = Path(settings.plugin_name).stem
        console.print("\n[cyan]Generated files:[/cyan]")
        console.print(f"  • {plugin_base} - Main.ba2")
        if settings.build_mode == BuildMode.CLEAN:
            console.print(f"  • {plugin_base} - Geometry.csg")
            console.print(f"  • {plugin_base}.cdx")

        # Post-build cleanup prompt (matches original batch file)
        if Confirm.ask("\nRemove working files?", default=True):
            console.print("\n[dim]Removing working files...[/dim]")
            try:
                cleanup_success: bool = builder.cleanup_working_files()
                if cleanup_success:
                    console.print("[green]✓ Working files cleaned up[/green]")
                else:
                    console.print("[yellow]⚠ Some working files could not be removed[/yellow]")
            except Exception as e:  # noqa: BLE001
                logger.error(f"Failed to clean up working files: {e}")
                console.print("[red]✗ An error occurred during cleanup.[/red]")

        return True

    console.print(f"\n[bold red]✗ Build failed at step: {builder.failed_step}[/bold red]")
    console.print("[yellow]You can resume from this step next time.[/yellow]")
    return False


def prompt_for_cleanup(settings: Settings) -> bool:
    """Prompt user to clean up existing previs files.

    Args:
        settings: Build settings

    Returns:
        True if cleanup was performed
    """
    plugin_base: str = Path(settings.plugin_name).stem

    console.print("\n[yellow]Cleanup mode - Remove existing previs files[/yellow]")
    console.print("\nThis will delete:")
    console.print(f"  • {plugin_base} - Main.ba2")
    console.print(f"  • {plugin_base} - Geometry.csg (if exists)")
    console.print(f"  • {plugin_base}.cdx (if exists)")
    console.print("  • Working files (CombinedObjects.esp, Previs.esp)")
    console.print("  • Temporary build directories")

    if not Confirm.ask("\nProceed with cleanup?", default=False):
        return False

    builder = PrevisBuilder(settings)

    try:
        with console.status("Cleaning up files..."):
            success: bool = builder.cleanup()
    except Exception as e:  # noqa: BLE001
        logger.error(f"Cleanup failed: {e}")
        success = False

    if success:
        console.print("\n[green]✓ Cleanup completed successfully![/green]")
    else:
        console.print("\n[red]✗ Some files could not be deleted.[/red]")

    return success


@click.command(context_settings={"ignore_unknown_options": True})
@click.argument("args", nargs=-1)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option(
    "--fallout4-path",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Override Fallout 4 installation directory (contains Fallout4.exe)",
)
@click.option("--xedit-path", type=click.Path(exists=True, dir_okay=False, path_type=Path), help="Override xEdit/FO4Edit executable path")
@click.option(
    "--build-mode",
    type=click.Choice(["clean", "filtered", "xbox"], case_sensitive=False),
    help="Build mode: clean (full rebuild), filtered (resume from filtered step), xbox (Xbox optimized)",
)
@click.option(
    "--archive-tool",
    type=click.Choice(["archive2", "bsarch"], case_sensitive=False),
    help="Archive tool to use: archive2 (default) or bsarch",
)
@click.option("--plugin", help="Plugin name to process (alternative to positional argument)")
def main(  # noqa: PLR0913
    args: tuple[str, ...],
    verbose: bool,
    fallout4_path: Path | None,
    xedit_path: Path | None,
    build_mode: str | None,
    archive_tool: str | None,
    plugin: str | None,
) -> None:
    """PyGeneratePrevisibines - Automated previs generation for Fallout 4.

    Usage:
        previs_builder.py [OPTIONS] [plugin.esp]

    Legacy batch file style (still supported):
        previs_builder.py [-clean|-filtered|-xbox] [-bsarch] [plugin.esp]

    Modern style:
        previs_builder.py --build-mode clean --plugin MyMod.esp
        previs_builder.py --build-mode filtered --archive-tool bsarch --plugin MyMod.esp

    Examples:
        previs_builder.py                           # Interactive mode
        previs_builder.py MyMod.esp                 # Process specific plugin
        previs_builder.py --build-mode filtered --plugin MyMod.esp
        previs_builder.py --archive-tool bsarch MyMod.esp
        previs_builder.py --fallout4-path "C:/Games/Fallout4" --xedit-path "C:/Tools/FO4Edit.exe" MyMod.esp
    """
    # Setup logging
    log_path = Path("PyGeneratePrevisibines.log")
    setup_logger(log_path, verbose=verbose)

    # Clear console and show banner
    console.clear()
    console.print(BANNER, style="bold cyan")

    # Check platform
    if sys.platform != "win32" or platform.system() != "Windows":
        console.print("[bold yellow]⚠ Warning:[/bold yellow] Running on non-Windows platform.")
        console.print("Some features may not work correctly.\n")

    try:
        # Process positional arguments (plugin name)
        final_plugin = plugin
        if args and not plugin:
            # First non-flag argument is the plugin name
            for arg in args:
                if not arg.startswith("-"):
                    final_plugin = arg
                    break
        
        # Process build mode and archive tool
        final_build_mode = build_mode
        final_use_bsarch = (archive_tool == "bsarch") if archive_tool else False
        
        # Handle legacy flags for backward compatibility
        for arg in args:
            if arg.startswith("-"):
                flag = arg.lower()
                if flag == "-clean" and not build_mode:
                    final_build_mode = "clean"
                elif flag == "-filtered" and not build_mode:
                    final_build_mode = "filtered"
                elif flag == "-xbox" and not build_mode:
                    final_build_mode = "xbox"
                elif flag == "-bsarch" and not archive_tool:
                    final_use_bsarch = True

        # Initialize settings with tool discovery and CLI overrides
        settings: Settings = Settings.from_cli_args(
            plugin_name=final_plugin,
            build_mode=final_build_mode,
            use_bsarch=final_use_bsarch,
            verbose=verbose,
            fallout4_path=fallout4_path,
            xedit_path=xedit_path,
        )

        # Validate tools only on Windows, as they are platform-specific
        if sys.platform == "win32":
            errors: list[str] = settings.tool_paths.validate()
            if errors:
                console.print("\n[bold red]⚠ Tool Configuration Issues:[/bold red]")
                for error in errors:
                    console.print(f"  • {error}")
                console.print("\n[red]Cannot proceed without required tools. Please fix the configuration and try again.[/red]")
                sys.exit(1)

        # Show tool versions (like the original batch file)
        show_tool_versions(settings)

        # Interactive mode if no plugin specified
        if not settings.plugin_name:
            # Check for cleanup mode
            if Confirm.ask("\nDo you want to clean up existing previs files?", default=False):
                plugin = prompt_for_plugin(settings)
                settings.plugin_name = plugin
                prompt_for_cleanup(settings)
                return

            # Normal build mode
            plugin = prompt_for_plugin(settings)
            settings.plugin_name = plugin

            # Prompt for build mode if not specified
            if not final_build_mode:
                settings.build_mode = prompt_for_build_mode()

        # Run the build
        result: bool | None = run_build(settings)

        # Handle exit codes: None is cancellation (OK), True is success (OK), False is failure
        if result is None:
            sys.exit(0)

        sys.exit(0 if result else 1)

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Build cancelled by user.[/yellow]")
        sys.exit(130)

    except Exception as e:  # noqa: BLE001
        console.print(f"\n[bold red]Unexpected error:[/bold red] {e}")
        if verbose:
            console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    main()
