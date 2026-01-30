"""Rate limiting for controlled message publishing."""

import time
from dataclasses import dataclass, field


@dataclass
class RateLimiter:
    """Token bucket rate limiter for message publishing."""

    rate: float  # Messages per second
    burst: int = 10  # Maximum burst size
    _tokens: float = field(init=False)
    _last_update: float = field(init=False)

    def __post_init__(self) -> None:
        """Initialize token bucket."""
        self._tokens = float(self.burst)
        self._last_update = time.monotonic()

    def _add_tokens(self) -> None:
        """Add tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self._last_update
        self._tokens = min(self.burst, self._tokens + elapsed * self.rate)
        self._last_update = now

    def acquire(self, count: int = 1) -> None:
        """Acquire tokens, blocking if necessary.

        Args:
            count: Number of tokens to acquire
        """
        self._add_tokens()

        while self._tokens < count:
            # Calculate sleep time to get enough tokens
            needed = count - self._tokens
            sleep_time = needed / self.rate
            time.sleep(sleep_time)
            self._add_tokens()

        self._tokens -= count

    def try_acquire(self, count: int = 1) -> bool:
        """Try to acquire tokens without blocking.

        Args:
            count: Number of tokens to acquire

        Returns:
            True if tokens were acquired, False otherwise
        """
        self._add_tokens()

        if self._tokens >= count:
            self._tokens -= count
            return True
        return False
