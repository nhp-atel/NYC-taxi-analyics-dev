"""Tests for rate limiter."""

import time

from src.producer.rate_limiter import RateLimiter


class TestRateLimiter:
    """Tests for the rate limiter."""

    def test_initial_burst(self):
        """Should allow initial burst."""
        limiter = RateLimiter(rate=10, burst=5)

        # Should be able to acquire burst immediately
        for _ in range(5):
            assert limiter.try_acquire()

        # Next one should fail (no tokens left)
        assert not limiter.try_acquire()

    def test_rate_replenishment(self):
        """Tokens should replenish over time."""
        limiter = RateLimiter(rate=100, burst=10)

        # Exhaust burst
        for _ in range(10):
            assert limiter.try_acquire()

        # Wait for some replenishment (0.05s = 5 tokens at 100/s)
        time.sleep(0.06)

        # Should have tokens again
        assert limiter.try_acquire()

    def test_acquire_blocking(self):
        """Acquire should block until tokens available."""
        limiter = RateLimiter(rate=100, burst=1)

        # Use the one token
        limiter.acquire()

        # Next acquire should block but complete
        start = time.monotonic()
        limiter.acquire()
        elapsed = time.monotonic() - start

        # Should have waited at least 0.01s (1 token at 100/s)
        assert elapsed >= 0.008  # Allow some slack

    def test_acquire_multiple(self):
        """Should be able to acquire multiple tokens."""
        limiter = RateLimiter(rate=100, burst=10)

        # Acquire 5 tokens
        limiter.acquire(5)

        # Should have 5 left
        for _ in range(5):
            assert limiter.try_acquire()

        assert not limiter.try_acquire()

    def test_max_burst(self):
        """Tokens should not exceed burst limit."""
        limiter = RateLimiter(rate=1000, burst=5)

        # Wait for a while
        time.sleep(0.1)

        # Should only have burst tokens available
        for _ in range(5):
            assert limiter.try_acquire()

        assert not limiter.try_acquire()
