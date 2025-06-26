#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from PrevisLib import BuildMode, Settings, setup_logger
from PrevisLib.utils.logging import get_logger

console = Console()
logger = get_logger(__name__)


@click.command()
@click.argument("plugin_name", required=False)
@click.option(
    "--build-mode",
    "-m",
    type=click.Choice(["clean", "filtered", "xbox"], case_sensitive=False),
    default="clean",
    help="Build mode to use",
)
@click.option("--bsarch", "-b", is_flag=True, help="Use BSArch instead of Archive2")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--no-prompt", is_flag=True, help="Skip interactive prompts")
def main(
    plugin_name: str | None,
    build_mode: str,
    bsarch: bool,
    verbose: bool,
    no_prompt: bool,
) -> None:
    setup_logger(verbose=verbose)
    
    console.print(
        Panel.fit(
            "[bold cyan]Automatic Previsbine Builder[/bold cyan]\n"
            "[dim]Python Port v0.1.0[/dim]",
            border_style="cyan",
        )
    )
    
    if sys.platform != "win32":
        console.print("[yellow]Warning:[/yellow] Running on non-Windows platform. Some features will be limited.")
    
    try:
        settings = Settings.from_cli_args(
            plugin_name=plugin_name,
            build_mode=build_mode,
            use_bsarch=bsarch,
            no_prompt=no_prompt,
            verbose=verbose,
        )
        
        errors = settings.validate_tools()
        if errors:
            console.print("\n[red]Tool validation errors:[/red]")
            for error in errors:
                console.print(f"  • {error}")
            
            if not no_prompt:
                console.print("\n[yellow]You can manually configure tool paths if needed.[/yellow]")
        
        if not settings.plugin_name and not no_prompt:
            plugin_name = console.input("\n[cyan]Enter plugin name:[/cyan] ").strip()
            if plugin_name:
                settings.plugin_name = plugin_name
        
        if settings.plugin_name:
            console.print(f"\n[green]Plugin:[/green] {settings.plugin_name}")
            console.print(f"[green]Build Mode:[/green] {settings.build_mode.value}")
            console.print(f"[green]Archive Tool:[/green] {settings.archive_tool.value}")
            
            table = Table(title="Tool Paths", show_header=True)
            table.add_column("Tool", style="cyan")
            table.add_column("Path", style="green")
            table.add_column("Status", style="yellow")
            
            tools = [
                ("Creation Kit", settings.tool_paths.creation_kit),
                ("xEdit/FO4Edit", settings.tool_paths.xedit),
                ("Archive2", settings.tool_paths.archive2),
                ("BSArch", settings.tool_paths.bsarch),
                ("Fallout 4", settings.tool_paths.fallout4),
            ]
            
            for tool_name, tool_path in tools:
                if tool_path:
                    status = "✓ Found" if tool_path.exists() else "✗ Not Found"
                    table.add_row(tool_name, str(tool_path), status)
                else:
                    table.add_row(tool_name, "Not configured", "✗")
            
            console.print("\n", table)
            
            if settings.ckpe_config_path:
                console.print(f"\n[green]CKPE Config:[/green] {settings.ckpe_config_path}")
            
            console.print("\n[yellow]Note:[/yellow] This is a foundation test. Build functionality not yet implemented.")
        else:
            console.print("\n[red]No plugin name provided. Exiting.[/red]")
            
    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        if verbose:
            console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    main()