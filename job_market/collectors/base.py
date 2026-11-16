"""Contracts and reusable controls for permitted source adapters."""

from collections.abc import Iterator
from dataclasses import dataclass
from time import monotonic, sleep
from typing import Protocol

from job_market.schemas import JobAdInput


class CollectorError(RuntimeError):
    """Raised when a source cannot be collected without silently losing evidence."""


class JobCollector(Protocol):
    source_name: str

    def collect(self) -> Iterator[JobAdInput]:
        """Yield validated advertisements from an authorized source."""


@dataclass
class RateLimiter:
    """Simple monotonic interval limiter for polite, source-scoped requests."""

    requests_per_second: float = 1.0
    _last_request: float | None = None

    def __post_init__(self) -> None:
        if self.requests_per_second <= 0:
            raise ValueError("requests_per_second must be positive")

    def wait(self) -> None:
        interval = 1 / self.requests_per_second
        if self._last_request is not None:
            remaining = interval - (monotonic() - self._last_request)
            if remaining > 0:
                sleep(remaining)
        self._last_request = monotonic()


def retry_delays(attempts: int = 3, initial_delay: float = 1.0, multiplier: float = 2.0) -> Iterator[float]:
    """Yield bounded exponential-backoff delays; adapters decide which errors are retryable."""
    if attempts < 1 or initial_delay < 0 or multiplier < 1:
        raise ValueError("invalid retry policy")
    for attempt in range(attempts):
        yield initial_delay * multiplier**attempt
