#!/usr/bin/env python3
"""Main entry point for PyGeneratePrevisibines."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskID, TextColumn
from rich.prompt import Confirm, Prompt
from rich.table import Table

from PrevisLib.config.settings import Settings
from PrevisLib.core import PrevisBuilder
from PrevisLib.models.data_classes import ArchiveTool, BuildMode, BuildStep
from PrevisLib.utils.logging import get_logger, setup_logger
from PrevisLib.utils.validation import validate_plugin_name

console = Console()
logger = get_logger(__name__)

# Banner art
BANNER = """
╔═══════════════════════════════════════════════════════════╗
║        Automatic Previsbine Builder for Fallout 4         ║
║                   Python Port v1.0.0                      ║
║              Based on GeneratePrevisibines.bat            ║
╚═══════════════════════════════════════════════════════════╝
"""


def parse_command_line(args: list[str]) -> tuple[str | None, BuildMode, bool]:
    """Parse command line arguments in the style of the original batch file.

    Args:
        args: Command line arguments (excluding script name)

    Returns:
        Tuple of (plugin_name, build_mode, use_bsarch)
    """
    plugin_name: str | None = None
    build_mode: BuildMode = BuildMode.CLEAN
    use_bsarch: bool = False

    for arg in args:
        if arg.startswith("-"):
            # Handle flags
            flag: str = arg.lower()
            if flag == "-clean":
                build_mode = BuildMode.CLEAN
            elif flag == "-filtered":
                build_mode = BuildMode.FILTERED
            elif flag == "-xbox":
                build_mode = BuildMode.XBOX
            elif flag == "-bsarch":
                use_bsarch = True
        # Assume it's the plugin name
        elif not plugin_name:
            plugin_name = arg

    return plugin_name, build_mode, use_bsarch


def prompt_for_plugin() -> str | None:
    """Prompt user for plugin name with validation.

    Returns:
        Valid plugin name or None if cancelled
    """
    console.print("\n[cyan]Enter the plugin name for previs generation.[/cyan]")
    console.print("[dim]Example: MyMod.esp[/dim]")

    while True:
        plugin_name: str = Prompt.ask("\nPlugin name", default="")

        if not plugin_name:
            if Confirm.ask("Exit without processing?", default=True):
                return None
            continue

        # Validate plugin name
        validation_result: tuple[bool, str] | str = validate_plugin_name(plugin_name)
        if isinstance(validation_result, tuple):
            is_valid, result_value = validation_result
            if not is_valid:
                console.print(f"\n[red]Error:[/red] {result_value}")
                continue
            plugin_name = result_value
        else:
            plugin_name = validation_result

        # Check for xPrevisPatch.esp
        if plugin_name.lower() == "xprevispatch.esp":
            console.print("\n[yellow]xPrevisPatch.esp is a special plugin used for testing.[/yellow]")
            if Confirm.ask("Do you want to rename it to something else?", default=True):
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


def run_build(settings: Settings) -> bool:
    """Execute the build process.

    Args:
        settings: Build settings

    Returns:
        True if successful, False otherwise
    """
    builder = PrevisBuilder(settings)

    # Check for previous failed build
    start_step: BuildStep | None = None
    if builder.failed_step:
        start_step = prompt_for_resume(builder)

    # Show summary
    show_build_summary(settings)

    if not Confirm.ask("\nProceed with build?", default=True):
        return False

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
            cleanup_success: bool = builder.cleanup_working_files()
            if cleanup_success:
                console.print("[green]✓ Working files cleaned up[/green]")
            else:
                console.print("[yellow]⚠ Some working files could not be removed[/yellow]")

    else:
        console.print(f"\n[bold red]✗ Build failed at step: {builder.failed_step}[/bold red]")
        console.print("[yellow]You can resume from this step next time.[/yellow]")

    return success


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

    with console.status("Cleaning up files..."):
        success: bool = builder.cleanup()

    if success:
        console.print("\n[green]✓ Cleanup completed successfully![/green]")
    else:
        console.print("\n[red]✗ Some files could not be deleted.[/red]")

    return success


@click.command(context_settings={"ignore_unknown_options": True})
@click.argument("args", nargs=-1)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def main(args: tuple[str, ...], verbose: bool) -> None:
    """PyGeneratePrevisibines - Automated previs generation for Fallout 4.

    Usage:
        previs_builder.py [-clean|-filtered|-xbox] [-bsarch] [plugin.esp]

    Examples:
        previs_builder.py                    # Interactive mode
        previs_builder.py MyMod.esp          # Process specific plugin
        previs_builder.py -filtered MyMod.esp # Filtered mode
        previs_builder.py -bsarch MyMod.esp   # Use BSArch tool
    """
    # Setup logging
    log_path = Path("PyGeneratePrevisibines.log")
    setup_logger(log_path, verbose=verbose)

    # Clear console and show banner
    console.clear()
    console.print(BANNER, style="bold cyan")

    # Check platform
    if sys.platform != "win32":
        console.print("[bold yellow]⚠ Warning:[/bold yellow] Running on non-Windows platform.")
        console.print("Some features may not work correctly.\n")

    try:
        # Parse command line arguments
        plugin_name, build_mode, use_bsarch = parse_command_line(list(args))

        # Initialize settings
        settings: Settings = Settings()
        settings.verbose = verbose

        # Apply command line options
        if plugin_name:
            is_valid, validated_name = validate_plugin_name(plugin_name)
            if is_valid:
                settings.plugin_name = validated_name
            else:
                console.print(f"[red]Invalid plugin name: {plugin_name}[/red]")
                return
        settings.build_mode = build_mode
        settings.archive_tool = ArchiveTool.BSARCH if use_bsarch else ArchiveTool.ARCHIVE2

        # Validate tools
        errors: list[str] = settings.tool_paths.validate()
        if errors:
            console.print("\n[bold red]⚠ Tool Configuration Issues:[/bold red]")
            for error in errors:
                console.print(f"  • {error}")
            console.print("\n[dim]Some tools are not found. The build may fail.[/dim]")

        # Interactive mode if no plugin specified
        if not settings.plugin_name:
            # Check for cleanup mode
            if Confirm.ask("\nDo you want to clean up existing previs files?", default=False):
                plugin = prompt_for_plugin()
                if plugin:
                    settings.plugin_name = plugin
                    prompt_for_cleanup(settings)
                    return

            # Normal build mode
            plugin = prompt_for_plugin()
            if not plugin:
                console.print("\n[yellow]No plugin selected. Exiting.[/yellow]")
                return

            settings.plugin_name = plugin

            # Prompt for build mode if not specified
            if not args or not any(arg.startswith("-") for arg in args):
                settings.build_mode = prompt_for_build_mode()

        # Run the build
        success: bool = run_build(settings)

        # Exit with appropriate code
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Build cancelled by user.[/yellow]")
        sys.exit(130)

    except (ValueError, OSError, RuntimeError) as e:
        console.print(f"\n[bold red]Unexpected error:[/bold red] {e}")
        if verbose:
            console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    main()
