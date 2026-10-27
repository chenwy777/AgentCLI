# AgentCLI

[![CI](https://github.com/chenwy777/AgentCLI/actions/workflows/ci.yml/badge.svg)](https://github.com/chenwy777/AgentCLI/actions/workflows/ci.yml)

AgentCLI Python 是一个运行在终端里的 AI Agent CLI，面向真实项目开发场景：读写文件、搜索代码、执行命令、联网检索、调用 MCP 工具、保存记忆、生成快照、恢复现场，并通过 Runtime API 对外提供线程、turn、事件和后台任务能力。

项目采用 Python 实现，围绕交互式终端、工具调用和可扩展的 Agent 运行流程组织代码，并为核心模块提供测试。

## 功能特性

- 交互式终端 Agent，基于 Rich 和 prompt-toolkit 渲染
- 单次 prompt 模式，适合脚本、管道和自动化调用
- OpenAI-compatible 流式 LLM 客户端，默认面向 DeepSeek 配置
- 支持 `DEEPSEEK_API_KEY` 等 provider-specific API Key
- ReAct 工具调用循环，支持 thinking、tool call、tool result、final output 和 usage 事件
- Plan-and-Execute 模式，使用独立 Planner 生成 DAG，并按依赖批次执行可并行任务
- Multi-Agent 协作模式，包含 Planner、Worker、Reviewer、依赖调度、并行 worker 和 review 重试
- 内置文件、Shell、grep、glob、记忆、网页搜索、网页抓取、代码搜索等工具
- HITL 人工确认、命令/路径安全策略和 JSONL 审计日志
- MCP client，支持 stdio 和 Streamable HTTP MCP server
- Skill 系统，支持内置、用户级和项目级 skill，支持启用/禁用和 `load_skill` 懒加载注入
- Chrome DevTools MCP 配置助手
- AgentCLI 自身也可以作为 MCP server 暴露内置工具
- Runtime API，支持线程、turn、事件日志和持久化后台任务
- SQLite 长期记忆和本地代码索引
- Agent run 前后自动创建快照，支持恢复现场
- 支持本地图片和远程图片输入，并根据模型能力自动降级

## 环境要求

- Python 3.11 或更新版本
- [uv](https://docs.astral.sh/uv/)
- 可选：`rg`，用于更快的本地搜索
- 可选：Chrome DevTools MCP 需要 Node.js 20.19.0 LTS 或更新版本、npm/npx 和 Chrome

## 快速开始

```bash
git clone https://github.com/chenwy777/AgentCLI.git
cd AgentCLI
uv sync --extra dev --locked
# 复制配置模板并填写自己的 API Key
cp .env.example .env
uv run agentcli --help
```

启动交互模式：

```bash
uv run agentcli
```

单次查询：

```bash
uv run agentcli -p "帮我总结这个项目"
```

检查当前环境：

```bash
uv run agentcli doctor --cwd .
```

## 配置

AgentCLI 的配置优先级如下：

1. 内置默认配置
2. `~/.agentcli/config.json`
3. 项目级 `.agentcli/config.json`
4. 项目级 `.env`
5. CLI 参数
6. 当前进程环境变量

可以把 DeepSeek Key 写到项目 `.env` 里：

```dotenv
AGENTCLI_PROVIDER=deepseek
AGENTCLI_MODEL=deepseek-v4-flash
DEEPSEEK_API_KEY=your_key_here
```

也可以使用 AgentCLI 通用 Key：

```dotenv
AGENTCLI_PROVIDER=deepseek
AGENTCLI_MODEL=deepseek-v4-flash
AGENTCLI_API_KEY=your_key_here
```

当前支持的 provider-specific API Key 包括：

- `DEEPSEEK_API_KEY`
- `GLM_API_KEY`
- `STEP_API_KEY`
- `KIMI_API_KEY`

通过命令行临时覆盖 provider 和 model：

```bash
uv run agentcli --provider deepseek --model deepseek-v4-flash
```

连接本地 OpenAI-compatible 服务：

```bash
AGENTCLI_PROVIDER=openai-compatible \
AGENTCLI_BASE_URL=http://127.0.0.1:11434/v1 \
AGENTCLI_MODEL=qwen2.5-coder \
uv run agentcli -p "解释这个仓库"
```

## 交互命令

进入 `uv run agentcli` 后，可以使用这些 slash commands：

```text
/help
/exit
/clear
/context
/memory
/memory search <query>
/memory clear
/save <fact>
/config
/tools
/hitl on|off|always|auto|never
/policy
/audit [N]
/index [path]
/search <query>
/plan <task>
/team <task>
/model
/skill
/skill list
/skill show <name>
/skill on <name>
/skill off <name>
/skill reload
/mcp
/task
/task add <task>
/task cancel <task_id>
/task log <task_id>
/snapshot
/snapshot clean
/restore <snapshot-id-or-index>
```

## 内置工具

AgentCLI 内置了一组 Agent 可以调用的本地工具和联网工具：

- `read_file`
- `write_file`
- `list_dir`
- `glob` / `glob_files`
- `grep` / `grep_code`
- `bash` / `execute_command`
- `web_search`
- `web_fetch`
- `save_memory`
- `load_skill`
- `search_code`
- `revert_turn`

写文件、执行命令、远程 MCP 写操作、恢复快照等危险动作，会经过 policy、HITL 和 audit 处理。

## 联网工具

`web_search` 使用 DuckDuckGo HTML 搜索，返回标题、URL 和摘要。

`web_fetch` 可以抓取公开 HTTP/HTTPS 页面，并做基础正文提取。它会拒绝 `file://`、loopback、私有网络和内网地址，降低 SSRF 风险。

如果需要登录态、浏览器状态或 JS 渲染页面，建议使用 Chrome DevTools MCP。

## MCP

AgentCLI 可以连接 MCP server，并把远端工具动态注册为：

```text
mcp__<server-name>__<tool-name>
```

初始化项目级 Chrome DevTools MCP 配置：

```bash
uv run agentcli mcp init-chrome --scope project
```

它会写入 `.agentcli/mcp.json`，内容类似：

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "type": "stdio",
      "command": "npx",
      "args": [
        "-y",
        "chrome-devtools-mcp@latest",
        "--no-usage-statistics"
      ]
    }
  }
}
```

连接已有 remote-debugging Chrome：

```bash
uv run agentcli mcp init-chrome \
  --scope project \
  --browser-url http://127.0.0.1:9222
```

查看已配置的 MCP server：

```bash
uv run agentcli mcp list
```

把 AgentCLI 自身作为 MCP server 暴露：

```bash
uv run agentcli mcp serve --transport stdio
uv run agentcli mcp serve --transport http --port 3000
```

HTTP smoke：

```bash
curl -sS -X POST http://127.0.0.1:3000 \
  -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

Chrome DevTools MCP 会把浏览器页面和 DevTools 状态暴露给 Agent。不要随意把包含个人账号、敏感数据或生产后台的 Chrome 会话授权给 Agent。

## Runtime API

AgentCLI 内置轻量 Runtime API，适合外部系统接入线程、turn、事件和后台任务。

启动服务：

```bash
AGENTCLI_RUNTIME_API_KEY=dev-key \
uv run agentcli serve --http --port 8080
```

创建线程：

```bash
curl -sS -X POST http://127.0.0.1:8080/v1/threads \
  -H 'x-api-key: dev-key'
```

发送 turn：

```bash
curl -sS -X POST http://127.0.0.1:8080/v1/threads/<thread_id>/turns \
  -H 'content-type: application/json' \
  -H 'x-api-key: dev-key' \
  -d '{"message":"总结这个项目"}'
```

读取事件：

```bash
curl -sS http://127.0.0.1:8080/v1/threads/<thread_id>/events \
  -H 'x-api-key: dev-key'
```

创建并查看后台任务：

```bash
curl -sS -X POST http://127.0.0.1:8080/v1/tasks \
  -H 'content-type: application/json' \
  -H 'x-api-key: dev-key' \
  -d '{"message":"后台总结这个仓库"}'

curl -sS http://127.0.0.1:8080/v1/tasks \
  -H 'x-api-key: dev-key'
```

## 图片输入

AgentCLI 支持在 prompt 里引用图片：

```text
分析这张截图 @image:./screenshots/page.png
```

也支持绝对路径和远程图片：

```text
解释这张图 @image:/Users/me/Desktop/diagram.png
看看这个图片 @image:https://example.com/image.png
```

本地图片会自动压缩、缩放，并在需要时把透明底铺成白底，再转为 data URL。如果当前 provider/model 不支持多模态输入，AgentCLI 会自动降级为文本元信息，不会把不支持的图片 payload 发给模型。

## 快照

每次 Agent run 都会尽力创建项目快照：

- `pre-turn`
- `post-turn`

快照保存在 `~/.agentcli/snapshots/`，不会写入项目 `.git`。

REPL 中可以使用：

```text
/snapshot
/restore 1
/snapshot clean
```

## SDK

```python
from agentcli.sdk import create_default_engine

engine = create_default_engine(cwd=".")
result = engine.ask_complete("解释这个项目")
print(result.text)

plan_result = engine.plan_complete("先读取 README，再总结项目结构")
team_result = engine.team_complete("让多个 Agent 并行检查核心模块")
```

## 开发

安装开发依赖：

```bash
uv sync --extra dev --locked
```

运行检查：

```bash
uv run python -m ruff check .
uv run python -m ruff format --check .
uv run python -m pytest
uv build
```

常用 smoke：

```bash
uv run agentcli --version
uv run agentcli --help
uv run agentcli doctor --cwd .
uv run agentcli --plain -p hello
```

## 能力说明

各模块能力与需要外部服务验证的项目见 [docs/capabilities.md](docs/capabilities.md)。

版本发布前的完整检查和打标签流程见 [docs/releasing.md](docs/releasing.md)。

## License

项目采用 MIT 许可证，原有版权声明保持不变，详见 [LICENSE](LICENSE)。
