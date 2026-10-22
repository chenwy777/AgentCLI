from __future__ import annotations

from pathlib import Path


class PathPolicyError(ValueError):
    pass


class PathGuard:
    """Restrict file tools to the current workspace tree."""

    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()

    def validate(self, value: str | Path) -> Path:
        candidate = Path(value)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        resolved = candidate.resolve()
        try:
            resolved.relative_to(self.root)
        except ValueError as exc:
            raise PathPolicyError(f"path escapes workspace: {value}") from exc
        return resolved
