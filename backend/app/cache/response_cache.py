
import hashlib
import time
import threading
from typing import Any, Optional


class ResponseCache:
    """
    In-memory cache for storing previously generated RAG responses.
    """

    def __init__(
        self,
        ttl_seconds: int = 300,
        max_entries: int = 1000,
    ):
        self.ttl = ttl_seconds
        self.max_entries = max_entries

        self._cache: dict[str, dict[str, Any]] = {}

        self._hits = 0
        self._misses = 0

        self._lock = threading.Lock()

    def _make_key(self, query: str, user_id: str) -> str:
        """
        Generate a unique hash using user ID and normalized query.
        """

        normalized_query = " ".join(query.lower().split())

        cache_text = f"{user_id}:{normalized_query}"

        return hashlib.sha256(
            cache_text.encode("utf-8")
        ).hexdigest()

    def get(
        self,
        query: str,
        user_id: str,
    ) -> Optional[Any]:
        """
        Retrieve a cached response if it exists and has not expired.
        """

        key = self._make_key(query, user_id)

        with self._lock:

            entry = self._cache.get(key)

            if entry is None:
                self._misses += 1
                return None

            current_time = time.monotonic()

            if current_time - entry["timestamp"] < self.ttl:
                self._hits += 1
                return entry["response"]

            # Remove expired entry.
            del self._cache[key]

            self._misses += 1
            return None

    def set(
        self,
        query: str,
        user_id: str,
        response: Any,
    ) -> None:
        """
        Store a response in the cache.
        """

        key = self._make_key(query, user_id)

        with self._lock:

            # Remove expired entries.
            current_time = time.monotonic()

            expired_keys = [
                cache_key
                for cache_key, entry in self._cache.items()
                if current_time - entry["timestamp"] >= self.ttl
            ]

            for cache_key in expired_keys:
                del self._cache[cache_key]

            # Prevent unlimited memory growth.
            if (
                key not in self._cache
                and len(self._cache) >= self.max_entries
            ):
                oldest_key = min(
                    self._cache,
                    key=lambda item: self._cache[item]["timestamp"],
                )

                del self._cache[oldest_key]

            self._cache[key] = {
                "response": response,
                "timestamp": current_time,
            }

    def clear(self) -> None:
        """Remove all cached responses."""

        with self._lock:
            self._cache.clear()

    @property
    def stats(self) -> dict:
        """Return cache performance statistics."""

        with self._lock:

            total_requests = self._hits + self._misses

            hit_rate = (
                self._hits / total_requests
                if total_requests > 0
                else 0.0
            )

            return {
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": f"{hit_rate:.2%}",
                "cached_entries": len(self._cache),
            }
