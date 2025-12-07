"""Cache compiled XSLT stylesheets."""

import os
from typing import Dict, Any, Optional, Tuple


class CacheManager:
    """Manage compiled stylesheet cache with file modification tracking."""

    def __init__(self):
        self._cache: Dict[str, Tuple[Any, float]] = {}  # {path: (stylesheet, mtime)}

    def get(self, template_path: str) -> Optional[Any]:
        """Get cached stylesheet if unchanged.

        Args:
            template_path: Absolute path to XSLT file

        Returns:
            Compiled stylesheet or None if not cached or file changed
        """
        if template_path not in self._cache:
            return None

        stylesheet, cached_mtime = self._cache[template_path]

        # Check if file was modified
        try:
            current_mtime = os.path.getmtime(template_path)
        except OSError:
            # File was deleted, invalidate cache
            del self._cache[template_path]
            return None

        if current_mtime != cached_mtime:
            # File changed, invalidate cache
            del self._cache[template_path]
            return None

        return stylesheet

    def set(self, template_path: str, stylesheet: Any):
        """Cache compiled stylesheet.

        Args:
            template_path: Absolute path to XSLT file
            stylesheet: Compiled stylesheet object
        """
        try:
            mtime = os.path.getmtime(template_path)
            self._cache[template_path] = (stylesheet, mtime)
        except OSError:
            # If file doesn't exist, don't cache
            pass

    def clear(self):
        """Clear entire cache."""
        self._cache.clear()

    def invalidate(self, template_path: str):
        """Invalidate specific template from cache.

        Args:
            template_path: Absolute path to XSLT file to invalidate
        """
        if template_path in self._cache:
            del self._cache[template_path]

    def size(self) -> int:
        """Get number of cached stylesheets."""
        return len(self._cache)

    def list_cached(self) -> list:
        """List all cached template paths."""
        return list(self._cache.keys())
