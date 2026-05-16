import time
import hashlib
import json
from typing import Any


class ResponseCache:
    """
    Cache para respuestas de providers.
    Reduce llamadas redundantes a APIs externas.
    """

    def __init__(self, default_ttl: int = 60):
        self._cache: dict[str, dict] = {}
        self._default_ttl = default_ttl

    def _make_key(self, provider_id: str, params: dict[str, Any]) -> str:
        raw = json.dumps({"provider_id": provider_id, "params": params}, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, provider_id: str, params: dict[str, Any]) -> Any | None:
        key = self._make_key(provider_id, params)
        entry = self._cache.get(key)
        if not entry:
            return None

        if time.monotonic() - entry["created_at"] > entry["ttl"]:
            del self._cache[key]
            return None

        return entry["data"]

    def set(
        self,
        provider_id: str,
        params: dict[str, Any],
        data: Any,
        ttl: int | None = None,
    ):
        key = self._make_key(provider_id, params)
        self._cache[key] = {
            "data": data,
            "provider_id": provider_id,
            "created_at": time.monotonic(),
            "ttl": ttl or self._default_ttl,
        }

    def invalidate(self, provider_id: str | None = None):
        if provider_id is None:
            self._cache.clear()
        else:
            keys_to_remove = [
                k for k, v in self._cache.items()
                if v.get("provider_id") == provider_id
            ]
            for k in keys_to_remove:
                del self._cache[k]

    def cleanup_expired(self):
        now = time.monotonic()
        expired = [
            k for k, v in self._cache.items()
            if now - v["created_at"] > v["ttl"]
        ]
        for k in expired:
            del self._cache[k]

    @property
    def size(self) -> int:
        return len(self._cache)

    def get_stats(self) -> dict:
        now = time.monotonic()
        total = len(self._cache)
        expired = sum(
            1 for v in self._cache.values()
            if now - v["created_at"] > v["ttl"]
        )
        return {
            "total_entries": total,
            "expired_entries": expired,
            "active_entries": total - expired,
        }


response_cache = ResponseCache(default_ttl=60)
