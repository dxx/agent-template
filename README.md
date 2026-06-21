# Agent Template

![python](https://img.shields.io/badge/language-python-4571A1)
[![MIT licensed](https://img.shields.io/github/license/dxx/agent-template.svg?color=98BB3E)](./LICENSE)

专用于 AI Agent 服务的项目模版，基于 LangChain + LangGraph 构建，支持多子代理协作、路由代理协作和人工审批流程。

## 技术栈

- **Python**: 3.12+
- **Web 框架**: FastAPI
- **Agent 框架**: LangChain + LangGraph
- **LLM**: OpenAI API (兼容)
- **包管理**: uv
- **服务器**: Uvicorn

## 项目结构

```
agent-template/
├── src/
│   ├── main.py                 # 应用入口
│   ├── config/                 # 配置管理
│   │   └── settings.py         # Pydantic Settings
│   ├── agent/                  # Agent 核心模块
│   │   ├── subagents/          # 子代理模块
│   │   │   ├── main.py         # 主 Agent 创建函数
│   │   │   ├── file_manager.py # 文件管理代理
│   │   │   ├── research.py     # 研究代理
│   │   │   ├── writing.py      # 写作代理
│   │   │   ├── review.py       # 审核代理
│   │   │   ├── greet.py        # 问候代理
│   │   │   ├── user.py         # 用户代理
│   │   │   └── agent_enum.py   # 子代理枚举
│   │   ├── router/             # 路由代理模块
│   │   │   ├── agent.py        # 路由模式主 Agent 创建函数
│   │   │   ├── file_manager.py # 路由文件管理代理
│   │   │   ├── research.py     # 路由研究代理
│   │   │   ├── writing.py      # 路由写作代理
│   │   │   ├── review.py       # 路由审核代理
│   │   │   └── greet.py        # 路由问候代理
│   │   ├── hitl/               # 人工介入模块
│   │   │   └── approve.py      # 审批内容生成
│   │   ├── llm/                # LLM 模型封装
│   │   │   └── model.py
│   │   ├── middleware/         # 中间件
│   │   │   ├── __init__.py     # 中间件导出
│   │   │   ├── local_filesystem.py  # 本地文件系统
│   │   │   ├── message_record.py    # 记录对话消息
│   │   │   ├── system_time.py  # 系统时间注入
│   │   │   └── prebuild/       # 预构建中间件
│   │   │       ├── skills.py   # Skills 支持
│   │   │       ├── subagents.py           # 子代理支持
│   │   │       ├── router_agent.py        # 路由代理支持
│   │   │       ├── tool_calls_patch.py    # 工具调用检查
│   │   │       ├── tool_error_handling.py # 工具调用错误处理
│   │   │       └── mcp_client.py          # MCP Client 中间件
│   │   ├── memory/             # 状态管理
│   │   │   ├── entry.py        # Checkpointer/Store 入口
│   │   │   ├── state.py        # Agent 状态定义
│   │   │   ├── router_state.py # 路由代理状态定义
│   │   │   ├── context.py      # Agent 上下文定义
│   │   │   ├── postgres_checkpointer.py  # Postgres Checkpointer
│   │   │   └── postgres_store.py         # Postgres Store
│   │   ├── prompts/            # 提示词
│   │   │   └── agent_prompts.py
│   │   └── tools/              # 工具函数
│   │       ├── file.py
│   │       ├── greet.py
│   │       └── user.py
│   ├── web/                    # Web 服务
│   │   ├── server.py           # FastAPI 应用
│   │   ├── api/                # API 路由
│   │   │   ├── __init__.py     # 路由模块导出
│   │   │   ├── health.py       # 健康检查路由
│   │   │   ├── chat.py         # 对话路由
│   │   │   ├── chat_router.py  # 路由 Agent 对话路由
│   │   │   └── message.py      # 消息管理路由
│   │   ├── middleware/         # 中间件
│   │   │   ├── auth.py         # 认证中间件
│   │   │   └── chat.py         # 对话状态中间件
│   │   ├── schemas/            # 数据模型
│   │   │   ├── chat.py         # 对话相关模型
│   │   │   ├── message.py      # 消息相关模型
│   │   │   ├── api.py          # API 通用模型
│   │   │   ├── api_code.py     # 响应码定义
│   │   │   └── state.py        # 应用状态模型
│   │   ├── service/            # 服务层
│   │   │   ├── chat_service.py # 对话服务
│   │   │   ├── chat_router_service.py # 路由 Agent 对话服务
│   │   │   └── message_service.py # 消息服务
│   │   └── session/            # 会话管理
│   │       ├── __init__.py
│   │       └── chat.py         # 对话会话管理
│   ├── log/                    # 日志模块
│   │   └── log.py
│   ├── utils/                  # 工具函数
│   │   ├── http_client.py
│   │   └── json_util.py
│   ├── exception/              # 异常定义
│   │   └── sys.py              # 系统异常
│   └── skills/                 # 技能目录
│       └── greet/              # 示例技能
│           ├── SKILL.md
│           └── references/
│               └── greet.md
├── tests/
│   ├── chat_api.http           # 对话 API 测试文件
│   └── message_api.http        # 消息 API 测试文件
├── pyproject.toml              # 项目配置
├── .env.example                # 环境变量示例
├── .env                        # 公共环境变量
├── .env.dev                    # 开发环境变量
├── .env.prod                   # 生产环境变量
├── .python-version             # Python 版本
├── LICENSE
└── README.md
```

## 核心模块

### Agent 模块 (`src/agent/`)

**主 Agent** - 通过 `create_main_agent()` 创建（位于 `subagents/main.py`），负责整体对话协调，通过 `task` 工具调度子代理。

**路由 Agent** - 通过 `create_router_agent()` 创建（位于 `router/agent.py`），使用 `RouteAgentMiddleware` 注册 `route` 工具。主 Agent 调用该工具后，内部 `StateGraph` 会先根据用户输入选择一个或多个路由任务代理，再并发调用对应代理并合并结果。

**状态与持久化** (`agent/memory/`):
- `entry.py`: Checkpointer 和 Store 的统一入口
  - `get_checkpointer()`: 获取当前 checkpointer（默认内存存储）
  - `get_store()`: 获取当前 store（默认内存存储）
- `AppAgentContext`: 用户上下文，包含 `user_id`
- `AppAgentState`: Agent 状态，继承自 `AgentState`，包含 `sub_agent_calls` 记录调用的子代理
- `RouterState`: 路由代理状态，包含 `query`、`routers`、`router`、`results` 和 `final_result`
- `init_postgres_checkpointer()` / `close_postgres_checkpointer()`: 初始化和关闭 Checkpointer 连接池
- `init_postgres_store()` / `close_postgres_store()`: 初始化和关闭 Store 连接池
- 默认使用内存存储 (`InMemorySaver` 和 `InMemoryStore`)，生产环境可切换为 PostgreSQL

**中间件系统**:

| 中间件 | 功能 |
|--------|------|
| `SubAgentMiddleware` | 子代理调度，通过 `task` 工具分发任务给子代理 |
| `RouteAgentMiddleware` | 路由代理调度，通过 `route` 工具自动选择并调用路由任务代理 |
| `SkillsMiddleware` | 技能系统支持，动态加载技能，向系统提示词注入可用技能列表 |
| `SummarizationMiddleware` | 消息超过 30 条或 token 超过 10000 时自动摘要 |
| `ToolCallsPatchMiddleware` | 检查工具调用是否正确执行，补充缺失的 ToolMessage |
| `ToolErrorHandlingMiddleware` | 工具调用错误时返回 ToolMessage，让 agent 继续运行 |
| `HumanInTheLoopMiddleware` | 人工介入，支持 approve/reject 决策 |
| `MCPClientMiddleware` | MCP Client 中间件，连接 MCP Server 并动态注入工具 |
| `FilesystemMiddleware` | 本地系统文件，提供本地文件操作工具 |
| `MessageRecordMiddleware` | 记录用户和 Agent 的对话消息 |
| `SystemTimeMiddleware` | 动态注入系统当前时间到提示词，帮助 Agent 准确回答时间相关问题 |

**子代理系统** (`subagents/`):

| 子代理 | 功能 |
|--------|------|
| `FileManagerAgent` | 文件管理（读取/写入） |
| `ReseachAgent` | 从多个信息源收集整理信息 |
| `WritingAgent` | 撰写高质量内容 |
| `ReviewAgent` | 审核文本并提供改进建议 |
| `GreetAgent` | 处理问候和基础交互 |
| `UserAgent` | 用户相关操作代理 |

**路由代理系统** (`router/`):

| 路由任务代理 | 功能 |
|--------------|------|
| `FileManagerAgent` | 文件管理（读取/写入），支持人工审批 |
| `ResearchAgent` | 从多个信息源收集整理信息 |
| `WritingAgent` | 撰写高质量内容 |
| `ReviewAgent` | 审核文本并提供改进建议 |
| `GreetAgent` | 处理问候和基础交互 |

**人工介入模块** (`hitl/`):
- `approve.py`: 审批内容生成，将工具调用转换为用户可读的审批信息

**MCP Client 中间件** (`prebuild/mcp_client.py`):
- `MCPClientMiddleware`: 连接 MCP (Model Context Protocol) Server，动态加载和注入工具
- 支持配置多个 MCP Server 连接
- 工具名称自动添加前缀以避免冲突（格式：`servername_toolname`）
- 支持 `ignore_tools` 参数屏蔽不需要的工具
- 支持 `callbacks` 和 `tool_interceptors` 扩展功能

**技能系统** (`skills/`):
- `SkillLoader`: 技能加载器抽象定义
- `DirectorySkillLoader`: 从本地目录加载技能
- `RemoteSkillLoader`: 从远程加载技能

**状态管理** (`memory/`):
- `AppAgentState`: Agent 运行状态，包含消息历史和子代理调用记录
- `AppAgentContext`: Agent 运行时上下文，包含用户信息

### Web 模块 (`src/web/`)

**服务** (`server.py`):
- 基于 FastAPI 的 REST 服务
- 全局异常处理（HTTPException、RequestValidationError、Exception）
- 认证中间件
- 生命周期管理（Postgres 连接初始化/关闭）

**路由** (`api/`):

| 路由 | 方法 | 功能 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/chat/stream` | POST | SSE 流式对话（需认证） |
| `/chat/router/stream` | POST | SSE 路由 Agent 流式对话（需认证） |
| `/message/chat/create` | POST | 创建新对话 |
| `/message/all` | GET | 获取用户所有对话 |
| `/message/chat/{chat_id}` | GET | 获取指定对话的消息列表 |
| `/message/chat/{chat_id}` | DELETE | 删除指定对话的所有消息 |
| `/message/all` | DELETE | 删除用户所有对话 |

**中间件** (`middleware/`):
- `AuthMiddleware`: 基于请求头认证，公开路径白名单: `/docs`, `/openapi.json`, `/health`, `/test/chat/stream`
- `ChatMiddleware`: 对话状态中间件，从请求中提取 `user_id` 和 `chat_id` 校验 `chat_id`


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

主要配置项：
- `OPENAI_PROVIDER`: 模型提供商，可选 `bailian`、`volcengine`、`deepseek`、`bigmodel`、`minimax`
- `OPENAI_API_KEY`: 你的 API Key
- `OPENAI_BASE_URL`: API 地址
- `OPENAI_MODEL`: 模型名称

### 3. 启动服务

```bash
uv run src/main.py
```

### 4. 测试

测试对话（无需认证）：
```
GET /test/chat/stream?user_id=test_user&chat_id=test_chat&content=你好
```

项目提供了完整的 HTTP 测试文件：
- `tests/chat_api.http` - 子代理模式对话 API 测试
- `tests/chat_router_api.http` - 路由模式对话 API 测试
- `tests/human-in-the-loop.http` - 人工介入 API 测试
- `tests/mcp.http` - MCP 工具 API 测试
- `tests/message_api.http` - 消息管理 API 测试
- `tests/multimodal_api.http` - 多模态 API 测试
- `tests/skills_api.http` - 技能 API 测试


## 环境配置

项目提供三套环境配置文件：
- `.env`      - 公共配置
- `.env.dev`  - 开发环境配置
- `.env.prod` - 生产环境配置

可增加额外的环境配置，配置文件名格式: `.env.环境名称`，然后在 `config/settings.py` 中增加对应的代码。


### 环境配置说明

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `APP_HOST` | 监听地址 | 127.0.0.1 |
| `APP_PORT` | 监听端口 | 8000 |
| `LOG_LEVEL` | 日志级别 (debug/info/warning/error) | info |
| `LOG_HANDLERS` | 日志处理方式 (console/file) | ["console"] |
| `LOG_FORMAT_TYPE` | 日志格式类型 (text/json) | text |
| `LOG_FILE` | 日志文件路径 | logs/app.log |
| `CORS_ALLOW_ORIGINS` | CORS 允许的 origins，JSON 数组格式 | 空 |
| `CORS_ALLOW_CREDENTIALS` | 是否允许跨域请求携带凭证 | false |
| `OPENAI_PROVIDER` | 模型提供商，可选：bailian、volcengine、deepseek、bigmodel、minimax | - (必填) |
| `OPENAI_BASE_URL` | OpenAI 兼容 API 地址，会自动补充 `/chat/completions` | - (必填) |
| `OPENAI_API_KEY` | API Key，可引用环境变量如 ${API_KEY} | - (必填) |
| `OPENAI_MODEL` | 模型名称 | - (必填) |
| `OPENAI_TEMPERATURE` | 温度参数 | 0.7 |
| `OPENAPI_URL` | Swagger 文档路径 (设为 "" 禁用) | /openapi.json |
| `POSTGRES_MEMORY_CONN_STR` | Postgres 连接字符串（用于 checkpointer 和 store） | - (必填) |


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

## 子代理调度

主 Agent 通过 `task` 工具调用子代理系统：

1. 用户请求 → 主 Agent 处理
2. 主 Agent 判断需要调用的子代理类型
3. 通过 `task(agent_name, task_input)` 分发给对应子代理
4. 子代理执行完成后返回结果
5. 主 Agent 整合结果返回给用户

## 路由代理调度

路由模式下，主 Agent 不直接决定子代理，而是调用 `route` 工具交给路由图处理：

1. 用户请求 → Router Main Agent 处理
2. Router Main Agent 调用 `route`
3. 工具从当前消息历史提取用户输入，构造 `{"query": 用户输入}`
4. 内部路由图根据代理描述选择一个或多个 `RouteTaskAgent`
5. 多个任务代理可并发执行
6. 单个结果直接返回，多个结果由合并模型整理为 `final_result`

## 人工审批流程

某些危险操作（如文件写入）会触发人工审批：

1. 工具调用 → `HumanInTheLoopMiddleware` → `interrupt()` 中断
2. 返回审批请求给前端（`msg_type=approve`）
3. 用户提交决策（`approve`/`reject`）
4. 处理决策后继续或返回错误

## 技能系统

技能存储在 `skills/` 目录下，每个技能为一个文件夹：

```
skills/
├── <skill-name>/
│   ├── SKILL.md          # 技能描述，YAML frontmatter + 技能内容
│   └── references/       # 参考文档目录（可选）
│       └── <ref-file>    # 参考文件
```

`SKILL.md` 格式：
```markdown
---
name: <skill-name>
description: <技能简短描述>
---

# 技能名称

技能详细描述和指令，引用参考文件。
```

技能中间件会：
1. 扫描 `skills/` 下所有子目录的 `SKILL.md`
2. 解析 YAML frontmatter 获取名称和描述
3. 生成可用技能列表并注入系统提示词
4. 通过 `load_skill` 工具按需加载技能详情和来源路径


## Swagger

### 开发地址

服务启动后访问 `http://127.0.0.1:8000/docs` 查看 API 文档。

### 生产禁用

生产环境通过配置 `OPENAPI_URL=""` 或环境变量禁用

## 更新日志

[CHANGELOG](./CHANGELOG.md)
