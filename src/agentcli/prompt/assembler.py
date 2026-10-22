from __future__ import annotations

from datetime import datetime
from pathlib import Path

from agentcli.config import AgentCLIConfig
from agentcli.memory import MemoryManager
from agentcli.skill import SkillRegistry


class PromptAssembler:
    def __init__(
        self,
        config: AgentCLIConfig,
        cwd: str,
        tool_names: list[str],
        model: str,
        provider: str,
    ):
        self.config = config
        self.cwd = str(Path(cwd).resolve())
        self.tool_names = tool_names
        self.model = model
        self.provider = provider

    def build(self) -> str:
        parts = [
            "You are AgentCLI, a powerful AI coding assistant running in a terminal.",
            f"Current time: {datetime.now().isoformat(timespec='seconds')}",
            f"Working directory: {self.cwd}",
            f"Model: {self.model} ({self.provider})",
            f"Available tools: {', '.join(self.tool_names)}",
            "",
            "Guidelines:",
            "- Be concise, direct, and implementation-oriented.",
            "- Use tools to inspect files, search code, and verify behavior when needed.",
            "- Prefer deterministic local tools before guessing.",
            "- When writing files, use write_file and keep changes scoped.",
            "- Preserve URLs and user-provided identifiers exactly unless a tool result proves "
            "otherwise.",
            "- Ask a clarifying question only when proceeding would be risky.",
        ]
        project_memory = self._project_memory()
        if project_memory:
            parts.extend(["", "Project memory:", project_memory])
        skill_index = SkillRegistry(self.cwd).index_text() if self.config.features.skill else ""
        if skill_index:
            parts.extend(["", skill_index])
        return "\n".join(parts)

    def _project_memory(self) -> str:
        memory_files = [
            Path(self.cwd) / "AGENT.md",
            Path(self.cwd) / ".agentcli" / "AGENT.md",
            Path(self.cwd) / "AGENT.local.md",
            Path(self.cwd) / ".agentcli" / "AGENT.local.md",
        ]
        chunks = []
        for path in memory_files:
            if path.exists():
                try:
                    chunks.append(path.read_text(encoding="utf-8")[:4000])
                except OSError:
                    continue
        if self.config.features.memory and self.config.memory.long_term_enabled:
            manager = MemoryManager(self.config.memory.long_term_db_path, scope=self.cwd)
            memories = manager.list(limit=8)
            if memories:
                chunks.append("\n".join(f"- {item.content}" for item in memories))
        return "\n\n".join(chunks)[:8000]
