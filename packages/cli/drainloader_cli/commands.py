import dataclasses
import sys
import time

from fnmatch import fnmatch
from pathlib import Path
from typing import Any

import drainloader as dl

from drainloader.exceptions import DrainloaderError
from drainloader.plugins import get_plugin_class
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    ProgressColumn,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.table import Table
from rich.text import Text

from drainloader_cli.io import download_file
from drainloader_cli.utils import console, sanitize_for_filesystem


class SmartDownloadColumn(DownloadColumn):
    """DownloadColumn that only shows for 'file' type tasks with a leading bullet."""
    def render(self, task: Any) -> Text:
        if task.fields.get("type") != "file":
            return Text("")
        return Text.assemble(("• ", "dim"), super().render(task))

class SmartTransferSpeedColumn(TransferSpeedColumn):
    """TransferSpeedColumn that only shows for 'file' type tasks with a leading bullet."""
    def render(self, task: Any) -> Text:
        if task.fields.get("type") != "file":
            return Text("")
        return Text.assemble(("• ", "dim"), super().render(task))

class SmartTimeRemainingColumn(TimeRemainingColumn):
    """TimeRemainingColumn that only shows for 'file' type tasks with a leading bullet."""
    def render(self, task: Any) -> Text:
        if task.fields.get("type") != "file":
            return Text("")
        return Text.assemble(("• ", "dim"), super().render(task))


def extract_command(url: str, output_json: bool) -> None:
    """Handle extract command logic."""
    try:
        if not output_json and (plugin_name := _get_plugin_name(url)):
            console.print(f"[green]✓[/green] Using plugin: [bold]{plugin_name}[/bold]")

        items = []
        if output_json:
            for item in dl.extract(url):
                items.append(item)
        else:
            with Progress(
                TextColumn("[bold blue]Extracting metadata..."),
                BarColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("", total=None)
                for item in dl.extract(url):
                    items.append(item)
                    progress.update(task, advance=1)

        if output_json:
            _print_json(url, items)
        else:
            _print_human_readable(items)

    except DrainloaderError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


def download_command(
    url: str,
    output_dir: str,
    flat: bool,
    pattern: str | None,
    options: dict[str, Any],
) -> None:
    """Handle download command logic."""
    try:
        if plugin_name := _get_plugin_name(url):
            console.print(f"[green]✓[/green] Using plugin: [bold]{plugin_name}[/bold]")

        items = []
        with Progress(
            TextColumn("[bold blue]Discovering files..."),
            BarColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("", total=None)
            for item in dl.extract(url, **options):
                items.append(item)
                progress.update(task, advance=1)

        if pattern:
            original_count = len(items)
            items = [item for item in items if fnmatch(item.filename, pattern)]
            console.print(f"[dim]Filtered: {original_count} → {len(items)} files[/dim]")

        if not items:
            console.print("[yellow]⚠ No files to download.[/yellow]")
            return

        console.print(f"[green]✓[/green] Found [bold]{len(items)}[/bold] files.")

        _download_with_progress(items, Path(output_dir), flat, options)

    except DrainloaderError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


def _download_with_progress(
    items: list[dl.DownloadItem],
    base_dir: Path,
    flat: bool,
    options: dict[str, Any],
) -> None:
    """Download all items with refined UI and a summary table."""
    results = []
    
    progress = Progress(
        TextColumn("[bold blue]{task.fields[filename]:<40}"),
        BarColumn(bar_width=None),
        "[progress.percentage]{task.percentage:>3.0f}%",
        SmartDownloadColumn(),
        SmartTransferSpeedColumn(),
        SmartTimeRemainingColumn(),
        console=console,
    )

    start_time = time.time()
    with progress:
        # Only add "Batch Progress" if there's more than one file
        overall = None
        if len(items) > 1:
            overall = progress.add_task(
                "Batch Progress",
                total=len(items),
                filename="Batch Progress",
                type="batch",
            )

        for item in items:
            if flat or not item.collection_name:
                dest_dir = base_dir
            else:
                dest_dir = base_dir / sanitize_for_filesystem(item.collection_name)

            dest_path = dest_dir / sanitize_for_filesystem(item.filename)

            # Important: set start=False here to fix speed accuracy on resumption
            file_task = progress.add_task(
                "download",
                filename=item.filename,
                start=False,
                type="file",
            )

            success = download_file(item, dest_path, progress, file_task, options)
            status = "Success" if success else "Failed"
            
            # Record size (actual on disk)
            actual_size = dest_path.stat().st_size if dest_path.exists() else 0
            results.append((item.filename, status, actual_size))

            progress.remove_task(file_task)
            
            # Update overall progress if it exists
            if overall is not None:
                progress.advance(overall)
                completed = int(progress.tasks[overall].completed)
                progress.update(overall, filename=f"Batch ({completed}/{len(items)})")

    total_time = time.time() - start_time
    _print_summary_table(results, base_dir, total_time)


def _print_summary_table(results: list, base_dir: Path, total_time: float) -> None:
    """Show a professional summary of the download batch."""
    console.print()
    table = Table(title="Download Summary", title_style="bold green", header_style="bold cyan", border_style="dim")
    table.add_column("File Name", overflow="fold")
    table.add_column("Status", justify="center")
    table.add_column("Size", justify="right")

    total_size = 0
    success_count = 0
    for name, status, size in results:
        style = "green" if status == "Success" else "red"
        size_str = f"{size / (1024*1024):.2f} MB"
        table.add_row(name, f"[{style}]{status}[/{style}]", size_str)
        if status == "Success":
            success_count += 1
            total_size += size

    console.print(table)
    
    success_style = "bold green" if success_count == len(results) else "bold yellow"
    console.print(f"[{success_style}]✓ Completed {success_count}/{len(results)} files[/{success_style}]")
    console.print(f"[dim]Total downloaded: {total_size / (1024*1024):.2f} MB in {total_time:.1f}s[/dim]")
    console.print(f"[dim]Location: {base_dir.absolute()}[/dim]\n")
    
    if success_count < len(results):
        sys.exit(1)


def _get_plugin_name(url: str) -> str | None:
    from urllib.parse import urlparse
    domain = urlparse(url).netloc
    plugin_class = get_plugin_class(domain)
    return plugin_class.__name__ if plugin_class else None


def _print_json(url: str, items: list[dl.DownloadItem]) -> None:
    data = {
        "source": url,
        "count": len(items),
        "items": [dataclasses.asdict(item) for item in items],
    }
    console.print_json(data=data)


def _print_human_readable(items: list[dl.DownloadItem]) -> None:
    console.print(f"\n[bold]Found {len(items)} files:[/bold]\n")
    for i, item in enumerate(items, 1):
        console.print(f"  [cyan]{i:02d}.[/cyan] {item.filename}")
        if item.collection_name:
            console.print(f"      [dim]Collection: {item.collection_name}[/dim]")
        if item.size_bytes:
            size_mb = item.size_bytes / (1024 * 1024)
            console.print(f"      [dim]Size: {size_mb:.2f} MB[/dim]")
