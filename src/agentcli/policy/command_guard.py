from __future__ import annotations

import re


class CommandPolicyError(ValueError):
    pass


class CommandGuard:
    """Fast-fail obviously destructive shell commands before HITL."""

    def __init__(self, blacklist: list[str] | None = None):
        self.blacklist = blacklist or []
        self.patterns = [
            re.compile(r"\brm\s+-[^\n]*r[^\n]*f\s+/(?:\s|$)"),
            re.compile(r"\brm\s+-[^\n]*r[^\n]*f\s+~(?:\s|$)"),
            re.compile(r"\bmkfs(?:\s|$)"),
            re.compile(r"\bdd\s+if=/dev/zero"),
            re.compile(r":\(\)\s*\{\s*:\|:&\s*\};:"),
            re.compile(r"\bchmod\s+-R\s+777\s+/"),
            re.compile(r"\bshutdown(?:\s|$)"),
            re.compile(r"\breboot(?:\s|$)"),
            re.compile(r"\bfind\s+/(\s|$)"),
        ]

    def validate(self, command: str) -> None:
        normalized = " ".join(command.strip().split())
        for blocked in self.blacklist:
            if blocked and blocked in normalized:
                raise CommandPolicyError(f"command rejected by policy: {blocked}")
        for pattern in self.patterns:
            if pattern.search(normalized):
                raise CommandPolicyError("command rejected by destructive-command policy")
