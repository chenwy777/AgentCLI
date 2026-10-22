# AgentCLI

AgentCLI 是使用 Python 实现的终端 AI Agent 项目。现有本地实现将按模块分批整理并导入本仓库，每批使用独立分支和 Pull Request，验证后再合并。

## 当前发布范围

当前 `main` 已导入前三批模块：

- Python 项目结构、依赖声明与锁定文件。
- 配置模型及加载逻辑：默认值、用户配置、项目配置、`.env`、命令行覆盖和进程环境变量。
- 消息、用量与查询结果等基础数据类型。
- 配置优先级及提供方 API Key 的测试。
- 命令与路径访问策略，以及敏感字段脱敏的审计日志。
- SQLite 长期记忆、本地代码索引和项目快照恢复。
- 用户/项目 Skill 注册、启停状态和提示上下文组装。
- Python 文件语法诊断，以及策略、快照和诊断测试。
- OpenAI 兼容模型客户端，以及 DeepSeek、OpenAI、智谱、Kimi 和阶跃星辰等提供方配置。
- 本地及远程图片引用处理，并为不支持视觉输入的模型生成文字说明。
- 网页搜索、公开网页抓取与本地网络地址访问限制。
- 文件读写、目录浏览、代码检索、命令执行、记忆与 Skill 加载等内置工具。

交互式 CLI、Agent 编排、MCP 与 Runtime API 尚未导入当前分支；本批次仍不提供 `agentcli` 终端命令。后续安排见 [分批发布计划](docs/release-plan.md)。

## 开发与验证

需要 Python 3.11 或更新版本，以及 uv。

```bash
git clone https://github.com/chenwy777/AgentCLI.git
cd AgentCLI
uv sync --extra dev --locked
uv run python -m pytest
uv run python -m ruff check .
uv run python -m ruff format --check .
uv build
```

`.env.example` 提供公开配置模板，真实密钥只应保存在本地 `.env` 中。已发布模块的测试使用本地临时目录和模拟配置，不需要真实 API Key。

## 配置示例

```python
from agentcli.config import load_config

config = load_config(project_root=".")
print(config.llm.provider)
print(config.llm.model)
```

配置文件位于 `~/.agentcli/config.json` 和项目内的 `.agentcli/config.json`。环境变量使用 `AGENTCLI_` 前缀；提供方专用密钥变量（如 `DEEPSEEK_API_KEY`）也受支持。

## License

项目采用 MIT 许可证，原有版权声明保持不变，见 [LICENSE](LICENSE)。
