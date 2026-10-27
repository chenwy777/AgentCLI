from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class McpServerSpec:
    name: str
    type: str = "stdio"
    command: str | None = None
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    cwd: str | None = None
    url: str | None = None
    headers: dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    timeout: float = 30.0


def load_mcp_server_specs(project_root: str | Path) -> dict[str, McpServerSpec]:
    root = Path(project_root).resolve()
    merged: dict[str, Any] = {}
    for path in [Path.home() / ".agentcli" / "mcp.json", root / ".agentcli" / "mcp.json"]:
        data = _read_json(path)
        if not data:
            continue
        servers = data.get("mcpServers", data)
        if isinstance(servers, dict):
            merged.update(servers)
    return {
        name: _spec_from_raw(name, raw, root)
        for name, raw in merged.items()
        if isinstance(raw, dict)
    }


def write_chrome_devtools_config(
    *,
    scope_root: str | Path | None = None,
    browser_url: str | None = None,
    headless: bool = False,
    slim: bool = False,
    no_usage_statistics: bool = True,
) -> Path:
    root = Path(scope_root).resolve() if scope_root else Path.home()
    config_dir = root / ".agentcli"
    config_dir.mkdir(parents=True, exist_ok=True)
    path = config_dir / "mcp.json"
    data = _read_json(path) or {"mcpServers": {}}
    servers = data.setdefault("mcpServers", {})
    args = ["-y", "chrome-devtools-mcp@latest"]
    if no_usage_statistics:
        args.append("--no-usage-statistics")
    if slim:
        args.append("--slim")
    if headless:
        args.append("--headless")
    if browser_url:
        args.append(f"--browser-url={browser_url}")
    servers["chrome-devtools"] = {
        "type": "stdio",
        "command": "npx",
        "args": args,
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _spec_from_raw(name: str, raw: dict[str, Any], project_root: Path) -> McpServerSpec:
    default_type = "streamable_http" if raw.get("url") else "stdio"
    server_type = str(raw.get("type") or raw.get("transport") or default_type)
    env = {
        key: _expand(str(value), project_root) for key, value in dict(raw.get("env") or {}).items()
    }
    args = [_expand(str(arg), project_root) for arg in raw.get("args") or []]
    cwd = raw.get("cwd")
    return McpServerSpec(
        name=name,
        type=server_type,
        command=_expand(str(raw["command"]), project_root) if raw.get("command") else None,
        args=args,
        env=env,
        cwd=_expand(str(cwd), project_root) if cwd else None,
        url=_expand(str(raw["url"]), project_root) if raw.get("url") else None,
        headers={
            key: _expand(str(value), project_root)
            for key, value in dict(raw.get("headers") or {}).items()
        },
        enabled=bool(raw.get("enabled", True)),
        timeout=float(raw.get("timeout", raw.get("startup_timeout", 30.0)) or 30.0),
    )


def _expand(value: str, project_root: Path) -> str:
    replacements = {
        "PROJECT_DIR": str(project_root),
        "HOME": str(Path.home()),
    }

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        return replacements.get(name, os.environ.get(name, ""))

    return re.sub(r"\$\{([^}]+)\}", replace, value)
