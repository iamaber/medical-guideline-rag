from collections import OrderedDict
from time import monotonic
from typing import Generic, Hashable, Optional, Tuple, TypeVar

V = TypeVar("V")


class TTLCache(Generic[V]):
    """Bounded in-memory cache whose entries expire after a fixed number of seconds."""

    def __init__(self, max_entries: int, ttl_seconds: float) -> None:
        self._max_entries = max_entries
        self._ttl_seconds = ttl_seconds
        self._entries: "OrderedDict[Hashable, Tuple[float, V]]" = OrderedDict()

    def get(self, key: Hashable) -> Optional[V]:
        entry = self._entries.get(key)
        if entry is None:
            return None
        stored_at, value = entry
        if monotonic() - stored_at > self._ttl_seconds:
            del self._entries[key]
            return None
        self._entries.move_to_end(key)
        return value

    def put(self, key: Hashable, value: V) -> None:
        self._entries[key] = (monotonic(), value)
        self._entries.move_to_end(key)
        while len(self._entries) > self._max_entries:
            self._entries.popitem(last=False)

    def clear(self) -> None:
        self._entries.clear()
