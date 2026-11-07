"""Errors surfaced to operators without leaking credentials."""


class TrackerError(Exception):
    """Expected application failure."""


class SourceError(TrackerError):
    """Remote source failed or returned an unusable page."""


class PriceUnavailable(SourceError):
    """No valid price can be extracted from the allowed source."""


class InvalidProduct(TrackerError):
    """Invalid input, configuration or product reference."""
