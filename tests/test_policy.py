from __future__ import annotations

import pytest

from agentcli.policy.command_guard import CommandGuard, CommandPolicyError
from agentcli.policy.path_guard import PathGuard, PathPolicyError


def test_path_guard_rejects_escape(tmp_path):
    guard = PathGuard(tmp_path)
    assert guard.validate("inside.txt") == tmp_path / "inside.txt"
    with pytest.raises(PathPolicyError):
        guard.validate("../outside.txt")


def test_command_guard_rejects_destructive_command():
    with pytest.raises(CommandPolicyError):
        CommandGuard().validate("rm -rf /")
