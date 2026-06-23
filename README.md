# Agent Template

![python](https://img.shields.io/badge/language-python-4571A1)
[![MIT licensed](https://img.shields.io/github/license/dxx/agent-template.svg?color=98BB3E)](./LICENSE)

专用于 AI Agent 服务的项目模版，基于 LangChain + LangGraph 构建，支持多子代理协作、路由代理协作和人工审批流程。

## 动机

AI 编程已经变成了日常开发方式。代码不再完全由人一行行敲出来，而是由开发者提出需求、AI 生成实现、再由人来审查和调整。但随之而来的问题也很明显：不同人使用不同提示词、不同模型、不同编码习惯，生成出来的代码风格、项目结构和实现方式很容易失控。尤其是在 Agent 项目中，流式对话、工具调用、子代理协作、记忆管理、人工审批、MCP 接入等模块交织在一起，如果每次都从零搭建，不仅容易重复造轮子，还会消耗大量 token 和开发时间。
这个项目正是为了解决这些问题而设计的。它不是一个简单的 Demo，而是一个面向 AI Agent 服务开发的工程模板，基于 FastAPI、LangChain 和 LangGraph 构建，内置了子代理协作、路由代理、Skills 技能系统、人工介入、多模态、MCP 工具接入和消息管理等能力。通过把常见的 Agent 架构、目录规范、配置方式和调用流程提前沉淀下来，开发者可以少写大量重复代码，也能让 AI 在更稳定的上下文和更统一的工程结构中生成代码，从而降低 token 成本，提高项目可维护性。

## 技术栈

- **Python**: 3.12+
- **Web 框架**: FastAPI
- **Agent 框架**: LangChain + LangGraph
- **LLM**: OpenAI API (兼容)
- **包管理**: uv
- **服务器**: Uvicorn

## 快速开始

### 1. 安装依赖

```bash
uv sync
```

### 2. 配置环境变量

复制环境变量示例文件并配置：

```bash
cp .env.example .env
```

### 3. 启动服务

```bash
uv run src/main.py
```

### 4. 测试

项目提供了完整的 HTTP 测试文件：
- `tests/chat_api.http` - 子代理模式对话 API 测试
- `tests/chat_router_api.http` - 路由模式对话 API 测试
- `tests/human-in-the-loop.http` - 人工介入 API 测试
- `tests/mcp.http` - MCP 工具 API 测试
- `tests/message_api.http` - 消息管理 API 测试
- `tests/multimodal_api.http` - 多模态 API 测试
- `tests/skills_api.http` - 技能 API 测试

## 对话流程

```
用户请求 → 认证中间件 → ChatService
                           ↓
                 MainAgent.astream() 异步流式处理
                           ↓
            ┌──────────────┴───────────────┐
            ↓                              ↓
        消息流 (messages)              更新流 (updates)
            ↓                              ↓
        渲染 AIMessageChunk           渲染完整消息/中断
            └───────────────┬──────────────┘
                            ↓
                        SSE 响应
```

## Swagger

### 开发地址

服务启动后访问 `http://127.0.0.1:8000/docs` 查看 API 文档。

### 生产禁用

生产环境通过配置 `OPENAPI_URL=""` 或环境变量禁用

## 详细文档

- [概要说明](./docs/resume.md)
- [环境配置](./docs/configs.md)
- [流式对话](./docs/chat.md)
- [子代理](./docs/subagents.md)
- [路由代理](./docs/router-agent.md)
- [人工介入](./docs/human-in-the-loop.md)
- [Skills](./docs/skills.md)
- [MCP](./docs/mcp.md)
- [多模态](./docs/multimodal.md)
- [历史消息](./docs/message.md)

## 前端

针对 agent-template 开发的 Web 前端项目 [agent-template-ui](https://github.com/dxx/agent-template-ui)。

## 更新日志

[CHANGELOG](./CHANGELOG.md)。
