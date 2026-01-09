"""
Drainloader - High-speed Pixeldrain downloader.
"""

from drainloader._api import extract
from drainloader.exceptions import (
    DrainloaderError,
    ExtractionError,
    UnsupportedDomainError,
)
from drainloader.item import DownloadItem

__version__ = "1.0.0"
__all__ = [
    "DownloadItem",
    "DrainloaderError",
    "ExtractionError",
    "UnsupportedDomainError",
    "extract",
]
