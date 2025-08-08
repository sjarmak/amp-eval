"""Rate limiting and circuit breaker for API calls."""

import time
import random
import logging
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from threading import Lock
from functools import wraps
from enum import Enum

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"          # Failing, block requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    requests_per_minute: int = 60
    requests_per_hour: int = 3000
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    jitter_factor: float = 0.1


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    success_threshold: int = 3
    
    # Cost protection thresholds
    max_tokens_per_hour: int = 100000
    max_cost_per_hour: float = 50.0  # USD


@dataclass
class RequestStats:
    """Track request statistics."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    last_reset: float = field(default_factory=time.time)
    request_times: list = field(default_factory=list)


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""
    pass


class CircuitBreakerOpen(Exception):
    """Raised when circuit breaker is open."""
    pass


class CostLimitExceeded(Exception):
    """Raised when cost limits are exceeded."""
    pass


class CircuitBreaker:
    """Circuit breaker with cost protection."""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        self.stats = RequestStats()
        self._lock = Lock()
    
    def _should_reset_stats(self) -> bool:
        """Check if hourly stats should be reset."""
        return time.time() - self.stats.last_reset > 3600
    
    def _reset_stats_if_needed(self):
        """Reset stats if an hour has passed."""
        if self._should_reset_stats():
            logger.info("Resetting hourly rate limit and cost stats")
            self.stats.total_tokens = 0
            self.stats.total_cost = 0.0
            self.stats.last_reset = time.time()
            # Keep only recent request times (last hour)
            cutoff = time.time() - 3600
            self.stats.request_times = [
                t for t in self.stats.request_times if t > cutoff
            ]
    
    def _check_cost_limits(self, estimated_tokens: int = 0, estimated_cost: float = 0.0):
        """Check if request would exceed cost limits."""
        if self.stats.total_tokens + estimated_tokens > self.config.max_tokens_per_hour:
            raise CostLimitExceeded(
                f"Token limit exceeded: {self.stats.total_tokens + estimated_tokens} > {self.config.max_tokens_per_hour}"
            )
        
        if self.stats.total_cost + estimated_cost > self.config.max_cost_per_hour:
            raise CostLimitExceeded(
                f"Cost limit exceeded: ${self.stats.total_cost + estimated_cost:.2f} > ${self.config.max_cost_per_hour:.2f}"
            )
    
    def can_request(self, estimated_tokens: int = 0, estimated_cost: float = 0.0) -> bool:
        """Check if request can proceed."""
        with self._lock:
            self._reset_stats_if_needed()
            
            # Check cost limits
            try:
                self._check_cost_limits(estimated_tokens, estimated_cost)
            except CostLimitExceeded:
                return False
            
            # Check circuit breaker state
            if self.state == CircuitState.OPEN:
                if time.time() - self.last_failure_time > self.config.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    logger.info("Circuit breaker transitioning to HALF_OPEN")
                else:
                    return False
            
            return True
    
    def record_success(self, tokens_used: int = 0, cost: float = 0.0):
        """Record successful request."""
        with self._lock:
            self.stats.successful_requests += 1
            self.stats.total_tokens += tokens_used
            self.stats.total_cost += cost
            self.stats.request_times.append(time.time())
            
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    logger.info("Circuit breaker CLOSED - service recovered")
    
    def record_failure(self):
        """Record failed request."""
        with self._lock:
            self.stats.failed_requests += 1
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.config.failure_threshold:
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker OPEN - {self.failure_count} consecutive failures")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics."""
        with self._lock:
            self._reset_stats_if_needed()
            return {
                'state': self.state.value,
                'total_requests': self.stats.total_requests,
                'successful_requests': self.stats.successful_requests,
                'failed_requests': self.stats.failed_requests,
                'failure_count': self.failure_count,
                'tokens_used_this_hour': self.stats.total_tokens,
                'cost_this_hour': self.stats.total_cost,
                'requests_this_hour': len(self.stats.request_times),
            }


class RateLimiter:
    """Rate limiter with exponential backoff and jitter."""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.request_times = []
        self._lock = Lock()
    
    def _clean_old_requests(self):
        """Remove request times older than tracking window."""
        now = time.time()
        cutoff_minute = now - 60
        cutoff_hour = now - 3600
        
        self.request_times = [t for t in self.request_times if t > cutoff_hour]
    
    def _get_requests_in_window(self, window_seconds: int) -> int:
        """Count requests in the given time window."""
        cutoff = time.time() - window_seconds
        return sum(1 for t in self.request_times if t > cutoff)
    
    def can_request(self) -> bool:
        """Check if request is allowed under rate limits."""
        with self._lock:
            self._clean_old_requests()
            
            requests_last_minute = self._get_requests_in_window(60)
            requests_last_hour = self._get_requests_in_window(3600)
            
            return (requests_last_minute < self.config.requests_per_minute and 
                   requests_last_hour < self.config.requests_per_hour)
    
    def record_request(self):
        """Record a new request."""
        with self._lock:
            self.request_times.append(time.time())
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        if not self.can_request():
            # Calculate wait time based on oldest request in minute window
            minute_requests = [t for t in self.request_times if t > time.time() - 60]
            if minute_requests:
                wait_time = 60 - (time.time() - min(minute_requests)) + 1
                logger.info(f"Rate limit reached, waiting {wait_time:.1f}s")
                time.sleep(wait_time)


def exponential_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter_factor: float = 0.1
):
    """Decorator for exponential backoff with jitter."""
    
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries:
                        raise
                    
                    # Calculate delay with exponential backoff and jitter
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    jitter = delay * jitter_factor * random.random()
                    total_delay = delay + jitter
                    
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {total_delay:.2f}s")
                    time.sleep(total_delay)
            
            return None
        return wrapper
    return decorator


# Global instances
_rate_limiter = RateLimiter(RateLimitConfig())
_circuit_breaker = CircuitBreaker(CircuitBreakerConfig())


def rate_limited(estimated_tokens: int = 0, estimated_cost: float = 0.0):
    """Decorator to apply rate limiting and circuit breaking."""
    
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check circuit breaker and cost limits
            if not _circuit_breaker.can_request(estimated_tokens, estimated_cost):
                if _circuit_breaker.state == CircuitState.OPEN:
                    raise CircuitBreakerOpen("Circuit breaker is open")
                else:
                    raise CostLimitExceeded("Cost or token limit would be exceeded")
            
            # Check rate limits
            _rate_limiter.wait_if_needed()
            _rate_limiter.record_request()
            
            try:
                result = func(*args, **kwargs)
                # Extract actual usage from result if available
                tokens_used = getattr(result, 'usage', {}).get('total_tokens', estimated_tokens)
                _circuit_breaker.record_success(tokens_used, estimated_cost)
                return result
            except Exception as e:
                _circuit_breaker.record_failure()
                raise
        
        return wrapper
    return decorator


def get_rate_limit_stats() -> Dict[str, Any]:
    """Get current rate limiting statistics."""
    return _circuit_breaker.get_stats()
