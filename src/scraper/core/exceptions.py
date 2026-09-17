"""Custom exceptions for the scraper."""


class ScraperError(Exception):
    """Base exception for all scraper errors."""


class RequestError(ScraperError):
    """Raised when an HTTP request fails after retries."""


class ParseError(ScraperError):
    """Raised when HTML/JSON parsing fails."""


class RateLimitError(ScraperError):
    """Raised when the target site rate-limits us."""


class ConfigurationError(ScraperError):
    """Raised for invalid configuration."""
