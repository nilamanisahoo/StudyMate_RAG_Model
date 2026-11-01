
import threading


class MetricsCollector:
    """
    Collect application performance metrics.
    """

    def __init__(self):

        self._requests_total = 0
        self._errors_total = 0

        self._latency_sum = 0.0
        self._latency_count = 0

        self._tokens_input = 0
        self._tokens_output = 0

        self._cache_hits = 0
        self._cache_misses = 0

        self._lock = threading.Lock()

    def record_request(
        self,
        latency_ms: float,
        input_tokens: int = 0,
        output_tokens: int = 0,
        error: bool = False,
        cache_hit: bool = False,
    ):
        """
        Record metrics for one API request.
        """

        with self._lock:

            self._requests_total += 1

            self._latency_sum += latency_ms
            self._latency_count += 1

            self._tokens_input += input_tokens
            self._tokens_output += output_tokens

            if error:
                self._errors_total += 1

            if cache_hit:
                self._cache_hits += 1
            else:
                self._cache_misses += 1

    def get_summary(self) -> dict:
        """
        Return a summary of collected metrics.
        """

        with self._lock:

            avg_latency = (
                self._latency_sum / self._latency_count
                if self._latency_count > 0
                else 0.0
            )

            error_rate = (
                self._errors_total / self._requests_total
                if self._requests_total > 0
                else 0.0
            )

            total_cache_requests = (
                self._cache_hits + self._cache_misses
            )

            cache_hit_rate = (
                self._cache_hits / total_cache_requests
                if total_cache_requests > 0
                else 0.0
            )

            return {
                "total_requests": self._requests_total,
                "total_errors": self._errors_total,
                "error_rate": f"{error_rate:.2%}",
                "avg_latency_ms": round(avg_latency, 2),
                "total_input_tokens": self._tokens_input,
                "total_output_tokens": self._tokens_output,
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses,
                "cache_hit_rate": f"{cache_hit_rate:.2%}",
            }
