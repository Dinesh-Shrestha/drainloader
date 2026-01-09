import signal
import sys
import threading

import click

from drainloader.plugins import PLUGIN_REGISTRY
from drainloader_cli.commands import download_command, extract_command
from drainloader_cli.utils import console, setup_logging


@click.group()
@click.version_option(prog_name="drainloader")
def cli() -> None:
    """
    Drainloader: High-speed downloader for Pixeldrain.

    Examples:
      drainloader extract https://pixeldrain.com/l/abc123
      drainloader download https://pixeldrain.com/u/xyz789 ./downloads
      drainloader download --aria2c https://pixeldrain.com/l/def456
    """


@cli.command(name="extract")
@click.argument("url")
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Output JSON instead of human-readable text",
)
@click.option("-v", "--verbose", is_flag=True, help="Enable debug logging")
def extract_cmd(url: str, output_json: bool, verbose: bool) -> None:
    """
    Extract metadata from URL without downloading (dry run).

    Shows what would be downloaded including filenames, sizes, and URLs.
    """
    setup_logging(verbose)
    extract_command(url, output_json)


@cli.command(name="download")
@click.argument("url")
@click.argument("output_dir", type=click.Path(), default="./downloads")
@click.option("-v", "--verbose", is_flag=True, help="Enable debug logging")
@click.option(
    "--flat",
    is_flag=True,
    help="Save all files to output_dir (no collection subfolders)",
)
@click.option(
    "--filter",
    "pattern",
    help="Filter files by glob pattern (e.g., *.jpg, *.mp4)",
)
@click.option(
    "--aria2c",
    is_flag=True,
    help="Use aria2c for downloads",
)
@click.option(
    "--aria2c-native",
    is_flag=True,
    help="Use native aria2c interface (shows detailed output)",
)
@click.option(
    "--aria2c-args",
    help="Additional arguments for aria2c",
)
@click.option(
    "--overwrite",
    is_flag=True,
    help="Overwrite existing files (default: resume/skip)",
)
def download_cmd(
    url: str,
    output_dir: str,
    verbose: bool,
    flat: bool,
    pattern: str | None,
    aria2c: bool,
    aria2c_native: bool,
    aria2c_args: str | None,
    overwrite: bool,
) -> None:
    """
    Download content from URL to OUTPUT_DIR.

    By default, files are organized into subfolders by collection.
    Use --flat to disable this behavior.
    """
    setup_logging(verbose)

    options = {
        "aria2c": aria2c,
        "aria2c_native": aria2c_native,
        "aria2c_args": aria2c_args,
        "overwrite": overwrite,
    }

    download_command(url, output_dir, flat, pattern, options)


@cli.command(name="plugins")
def list_plugins_cmd() -> None:
    """List all supported websites and domains."""
    console.print("\n[bold]Supported Platforms:[/bold]\n")

    for domain in sorted(PLUGIN_REGISTRY.keys()):
        plugin = PLUGIN_REGISTRY[domain]
        console.print(f"  • [cyan]{domain:<20}[/cyan] ({plugin.__name__})")

    console.print()


def signal_handler(sig, frame):
    sys.exit(1)


def main():
    signal.signal(signal.SIGINT, signal_handler)

    # Run in a daemon thread for responsive interruption
    main_thread = threading.Thread(target=cli)
    main_thread.daemon = True
    main_thread.start()

    while main_thread.is_alive():
        main_thread.join(timeout=0.1)


if __name__ == "__main__":
    main()
