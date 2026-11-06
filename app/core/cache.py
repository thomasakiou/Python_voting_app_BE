import time
from typing import Any, Optional, Dict

class SimpleTTLCache:
    """Thread-safe, lightweight in-memory TTL cache for high performance under load."""
    def __init__(self):
        self._cache: Dict[str, tuple[Any, float]] = {}

    def get(self, key: str) -> Optional[Any]:
        if key not in self._cache:
            return None
        value, expiry = self._cache[key]
        if time.time() > expiry:
            del self._cache[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl_seconds: int = 5) -> None:
        self._cache[key] = (value, time.time() + ttl_seconds)

    def delete(self, key: str) -> None:
        if key in self._cache:
            del self._cache[key]

    def clear(self) -> None:
        self._cache.clear()

    def invalidate_prefix(self, prefix: str) -> None:
        keys_to_del = [k for k in self._cache.keys() if k.startswith(prefix)]
        for k in keys_to_del:
            del self._cache[k]

cache = SimpleTTLCache()
