import logging
from collections.abc import Generator

from drainloader.exceptions import ExtractionError
from drainloader.item import DownloadItem
from drainloader.plugin import BasePlugin

logger = logging.getLogger(__name__)


class PixelDrain(BasePlugin):
    """
    Plugin for pixeldrain.com content extraction.
    Supports individual files and lists.
    """

    def extract(self) -> Generator[DownloadItem, None, None]:
        if "/u/" in self.url:
            yield from self._extract_file(self.url)
        elif "/l/" in self.url:
            yield from self._extract_list(self.url)
        else:
            msg = f"Unsupported PixelDrain URL format: {self.url}"
            raise ExtractionError(msg)

    def _extract_file(self, url: str) -> Generator[DownloadItem, None, None]:
        file_id = url.split("/")[-1]
        api_url = f"https://pixeldrain.com/api/file/{file_id}/info"

        response = self.session.get(api_url)
        response.raise_for_status()
        data = response.json()

        if not data.get("success"):
            msg = f"Failed to get file info: {data.get('message')}"
            raise ExtractionError(msg)

        yield DownloadItem(
            download_url=f"https://pixeldrain.com/api/file/{file_id}?download",
            filename=data.get("name", "unknown"),
            size_bytes=data.get("size", 0),
        )

    def _extract_list(self, url: str) -> Generator[DownloadItem, None, None]:
        list_id = url.split("/")[-1]
        api_url = f"https://pixeldrain.com/api/list/{list_id}"

        response = self.session.get(api_url)
        response.raise_for_status()
        data = response.json()

        if not data.get("success"):
            msg = f"Failed to get list info: {data.get('message')}"
            raise ExtractionError(msg)

        collection_name = data.get("title", "pixeldrain_list")
        for file_entry in data.get("files", []):
            file_id = file_entry.get("detail_id")
            yield DownloadItem(
                download_url=f"https://pixeldrain.com/api/file/{file_id}?download",
                filename=file_entry.get("name", "unknown"),
                size_bytes=file_entry.get("size", 0),
                collection_name=collection_name,
            )
