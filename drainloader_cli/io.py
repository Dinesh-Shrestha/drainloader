import os
import re
import shlex
import subprocess
import time

from pathlib import Path
from typing import Any

import requests

from drainloader.item import DownloadItem
from rich.progress import Progress, TaskID


def _parse_size(size_str: str, unit: str) -> int:
    """Convert aria2c size strings (e.g. 1.1GiB) to bytes."""
    units = {
        "B": 1,
        "KiB": 1024,
        "MiB": 1024**2,
        "GiB": 1024**3,
        "TiB": 1024**4,
        "K": 1024,
        "M": 1024**2,
        "G": 1024**3,
    }
    try:
        # Clean unit of any trailing non-alphabet characters
        unit = "".join(filter(str.isalpha, unit))
        return int(float(size_str) * units.get(unit, 1))
    except (ValueError, TypeError):
        return 0


def _build_aria2_cmd(item: DownloadItem, destination: Path, aria2_args: str | None = None, quiet: bool = True) -> list[str]:
    """Internal helper to build high-performance aria2c commands."""
    cmd = [
        "aria2c",
        item.download_url,
        "-o",
        destination.name,
        "-d",
        str(destination.parent),
        "--file-allocation=none",
        "--auto-file-renaming=false",
        "--allow-overwrite=true",
        "--continue=true",
    ]
    
    if quiet:
        cmd.extend(["--console-log-level=notice", "--summary-interval=1"]) # Notice + 1s for parsing
    
    if aria2_args:
        cmd.extend(shlex.split(aria2_args))
    else:
        # High-performance defaults
        cmd.extend(["-x", "8", "-s", "8", "--min-split-size=1M"])

    if item.headers:
        for key, value in item.headers.items():
            cmd.append(f"--header={key}: {value}")
            
    return cmd


def aria2_download(
    item: DownloadItem,
    destination: Path,
    progress: Progress,
    task_id: TaskID,
    aria2c_args: str | None = None,
) -> bool:
    """Download a file using aria2c with precision parsing of its output."""
    cmd = _build_aria2_cmd(item, destination, aria2c_args, quiet=True)

    # Regex to match user's sample: [#cf9351 19MiB/1.3GiB(1%) CN:8 DL:0.9MiB ETA:22m24s]
    # Breaks down into:
    # 1: Current size (19)
    # 2: Current unit (MiB)
    # 3: Total size (1.3)
    # 4: Total unit (GiB)
    # 5: Percentage (1)
    # 6: Speed value (0.9)
    # 7: Speed unit (MiB)
    # 8: ETA string (22m24s)
    summary_pattern = re.compile(
        r"\[#\w+\s+([\d.]+)(\w+)/([\d.]+)(\w+)\((\d+)%\).*?DL:([\d.]+)(\w+)(?:\s+ETA:([\w\d]+))?\]"
    )

    proc = None
    try:
        # Start aria2c and capture its output
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )

        progress.start_task(task_id)

        if proc.stdout:
            for line in proc.stdout:
                match = summary_pattern.search(line)
                if match:
                    curr_val, curr_u, total_val, total_u, pct, spd_val, spd_u, eta = match.groups()
                    
                    completed_bytes = _parse_size(curr_val, curr_u)
                    total_bytes = _parse_size(total_val, total_u)
                    
                    # Update progress bar with exact data from aria2c
                    progress.update(
                        task_id,
                        completed=completed_bytes,
                        total=total_bytes if total_bytes > 0 else (item.size_bytes or 0),
                    )
                
        proc.wait()
        return proc.returncode == 0

    except Exception:
        if proc:
            try:
                proc.terminate()
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
        return False


def download_file(
    item: DownloadItem,
    destination: Path,
    progress: Progress,
    task_id: TaskID,
    options: dict[str, Any] | None = None,
) -> bool:
    """
    Download a file with progress tracking, resumption support, and aria2c fallback.
    """
    options = options or {}
    use_aria2 = options.get("aria2c", False)
    use_native = options.get("aria2c_native", False)
    aria2_args = options.get("aria2c_args")
    overwrite = options.get("overwrite", False)

    try:
        destination.parent.mkdir(parents=True, exist_ok=True)

        if use_aria2 and use_native:
            progress.stop()
            cmd = _build_aria2_cmd(item, destination, aria2_args, quiet=False)
            subprocess.run(cmd)
            progress.start()
            return destination.exists()

        resume_byte = 0
        if destination.exists() and not overwrite:
            is_aria2_incomplete = use_aria2 and Path(str(destination) + ".aria2").exists()
            
            if not is_aria2_incomplete:
                current_size = destination.stat().st_size
                if item.size_bytes and current_size >= item.size_bytes:
                    progress.console.print(f"[yellow]⊙[/yellow] Skipped (complete): {item.filename}")
                    progress.update(task_id, completed=item.size_bytes, total=item.size_bytes)
                    return True
                
                resume_byte = current_size
                progress.console.print(f"[dim]⟳ Resuming {item.filename} from {resume_byte} bytes[/dim]")

        if use_aria2:
            progress.update(task_id, description=f"[bold green]Downloading: {item.filename}")
            success = aria2_download(item, destination, progress, task_id, aria2_args)
            if success:
                return True
            progress.console.print(f"[yellow]⚠[/yellow] aria2c failed for {item.filename}, falling back...")

        # Standard Downloader (Requests)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            **item.headers,
        }
        
        if resume_byte > 0:
            headers["Range"] = f"bytes={resume_byte}-"

        with requests.get(
            item.download_url,
            stream=True,
            timeout=60,
            headers=headers,
        ) as response:
            if resume_byte > 0 and response.status_code != 206:
                progress.console.print("[yellow]⚠ Server does not support resumption, restarting...[/yellow]")
                resume_byte = 0
                mode = "wb"
            else:
                mode = "ab" if resume_byte > 0 else "wb"

            response.raise_for_status()
            total_size = int(response.headers.get("content-length", 0)) + resume_byte
            
            progress.update(task_id, total=total_size, completed=resume_byte)
            progress.start_task(task_id)

            with destination.open(mode) as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        progress.advance(task_id, len(chunk))

        return True

    except (requests.RequestException, OSError) as e:
        progress.console.print(f"[red]✗[/red] Failed: {item.filename} ({e!s})")
        return False
