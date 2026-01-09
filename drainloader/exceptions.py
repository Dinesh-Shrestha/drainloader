class DrainloaderError(Exception):
    """Base exception for all drainloader errors."""


class ExtractionError(DrainloaderError):
    """Failed to extract items from URL due to network or parsing error."""


class UnsupportedDomainError(DrainloaderError):
    """No plugin available for this domain."""

    def __init__(self, domain: str) -> None:
        super().__init__(f"No plugin found for domain: {domain}")
        self.domain = domain
