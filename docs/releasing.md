# 发布检查

AgentCLI 使用锁定依赖和 GitHub Actions 验证每个 Pull Request 及 `main` 分支提交。CI 在 Ubuntu 和 Windows 上分别使用 Python 3.11 与 3.13，运行静态检查、格式检查、测试、CLI smoke 和构建。

## 本地发布前检查

```bash
uv sync --extra dev --locked
uv run python -m ruff check .
uv run python -m ruff format --check .
uv run python -m pytest
uv run agentcli --version
uv run agentcli --help
uv run agentcli doctor --cwd .
uv build
```

测试不需要真实模型密钥。真实 LLM、Chrome DevTools MCP 和 Runtime turn 的联调需要外部服务，应在准备对应环境后单独验证。

## 创建版本

1. 在 `pyproject.toml` 和 `src/agentcli/__init__.py` 中更新同一个版本号。
2. 更新 README 或能力说明中与该版本相关的内容。
3. 提交 Pull Request，并等待所有 CI 矩阵任务通过。
4. 合并后，从最新 `main` 创建带 `v` 前缀的标签，例如 `v0.1.0`。
5. 再次核对源码包和 wheel 内容，然后创建 GitHub Release 并上传构建产物。

```bash
git switch main
git pull --ff-only
git tag -a v0.1.0 -m "AgentCLI v0.1.0"
git push origin v0.1.0
```

仓库当前没有自动发布到 PyPI 的工作流。发布到包索引前，应另外配置可信发布、包名所有权和发布环境保护规则。
