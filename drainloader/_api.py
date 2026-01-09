import logging
import urllib.parse
from collections.abc import Generator
from typing import Any

from drainloader.exceptions import (
    ExtractionError,
    UnsupportedDomainError,
)
from drainloader.item import DownloadItem
from drainloader.plugins import get_plugin_class

logging.getLogger(__name__).addHandler(logging.NullHandler())
logger = logging.getLogger(__name__)


def extract(url: str, **options: Any) -> Generator[DownloadItem, None, None]:
    """
    Extract downloadable items from a Pixeldrain URL.

    Returns a generator that yields items lazily as they're discovered.
    Network requests happen during iteration, not at call time.

    Args:
        url: The source URL to extract from
        **options: Plugin-specific options

    Yields:
        DownloadItem: Metadata for each downloadable file
    """
    if not url or not url.strip():
        msg = "URL cannot be empty"
        raise ValueError(msg)

    url = url.strip()
    parsed = urllib.parse.urlparse(url)

    if not parsed.netloc:
        msg = f"Invalid URL: Could not parse domain from '{url}'"
        raise ValueError(msg)

    plugin_class = get_plugin_class(parsed.netloc)
    if plugin_class is None:
        raise UnsupportedDomainError(parsed.netloc)

    logger.debug(
        "Initializing %s for domain '%s'", plugin_class.__name__, parsed.netloc
    )

    try:
        plugin = plugin_class(url, **options)
        yield from plugin.extract()
    except (UnsupportedDomainError, ValueError):
        raise
    except Exception as e:
        logger.debug("Extraction failed for %r: %r", url, e, exc_info=True)
        msg = f"Failed to extract from {url}: {e}"
        raise ExtractionError(msg) from e
