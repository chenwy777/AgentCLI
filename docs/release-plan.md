# 分批发布计划

本仓库按依赖顺序导入已有的本地实现。每批只发布对应文件，通过独立分支、PR、验证和 merge commit 保留可审查的变更历史。它们是源码整理与导入记录，不是回填的开发时间线。

| 批次 | 范围 | 分支 | 状态 |
| --- | --- | --- | --- |
| 1 | 项目基础、配置与数据类型、配置测试 | `feat/project-foundation` | 已合并 |
| 2 | 权限策略、记忆、快照、代码索引、Skill 与提示上下文 | `feat/context-and-safety` | 已合并 |
| 3 | 模型客户端、图片、联网与本地工具执行 | `feat/model-and-tools` | 已合并 |
| 4 | ReAct、规划执行、多 Agent 编排与 SDK | `feat/agent-orchestration` | 已合并 |
| 5 | MCP、初始化装配、Runtime API 与后台任务 | `feat/mcp-and-runtime` | 已合并 |
| 6 | 交互式终端、渲染、命令入口与完整使用文档 | `feat/interactive-cli` | 当前发布批次 |
| 7 | 自动化验证与发布说明 | `ci/release-checks` | 未发布 |

后续批次在维护者准备继续发布时再推进，不会在本批次自动上传。
