# Agent Template

专用于 AI Agent 服务的项目模版，基于 LangChain + LangGraph 构建，支持多子代理协作和人工审批流程。

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
│   │   ├── subagents/           # 子代理模块
│   │   │   ├── main.py         # 主 Agent 创建函数
│   │   │   ├── file_manager.py # 文件管理代理
│   │   │   ├── research.py     # 研究代理
│   │   │   ├── writing.py      # 写作代理
│   │   │   ├── review.py       # 审核代理
│   │   │   ├── greet.py        # 问候代理
│   │   │   ├── user.py         # 用户代理
│   │   │   └── agent_enum.py   # 子代理枚举
│   │   ├── hitl/               # 人工介入模块
│   │   │   └── approve.py      # 审批内容生成
│   │   ├── llm/                # LLM 模型封装
│   │   │   └── model.py
│   │   ├── middleware/         # 中间件
│   │   │   ├── skills.py       # Skills 支持
│   │   │   ├── subagents.py    # 子代理支持
│   │   │   ├── system_time.py  # 系统时间注入
│   │   │   └── tool_calling_check.py # 工具调用检查
│   │   ├── memory/             # 状态管理
│   │   │   ├── state.py        # Agent 状态定义
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
│   │   ├── api/routes.py       # API 路由
│   │   ├── middleware/         # 中间件
│   │   │   └── auth.py         # 认证中间件
│   │   ├── schemas/            # 数据模型
│   │   │   ├── chat.py         # 对话相关模型
│   │   │   ├── api.py          # API 通用模型
│   │   │   ├── api_code.py     # 响应码定义
│   │   │   └── state.py        # 应用状态模型
│   │   └── service/            # 服务层
│   │       └── chat_service.py # 对话服务
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
├── tests/
│   └── test_api.http           # API 测试文件
├── pyproject.toml              # 项目配置
├── .env.example                # 环境变量示例
├── .env.dev.example            # 开发环境变量示例
├── .env.prod.example           # 生产环境变量示例
├── LICENSE
└── README.md
```

## 核心模块

### Agent 模块 (`src/agent/`)

**主 Agent** - 通过 `create_main_agent()` 创建（位于 `subagents/main.py`），负责整体对话协调，通过 `task` 工具调度子代理。

**状态与持久化** (`agent/memory/`):
- `AppAgentContext`: 用户上下文，包含 `user_id`
- `AppAgentState`: Agent 状态，继承自 `AgentState`，包含 `sub_agent_calls` 记录调用的子代理
- `async_postgres_checkpointer`: PostgreSQL 检查点，支持会话恢复
- `async_postgres_store`: PostgreSQL 存储，用于持久化数据
- `init_postgres_checkpointer()` / `close_postgres_checkpointer()`: 初始化和关闭 Checkpointer 连接池
- `init_postgres_store()` / `close_postgres_store()`: 初始化和关闭 Store 连接池
- 默认使用内存存储 (`InMemorySaver` 和 `InMemoryStore`)，生产环境可切换为 PostgreSQL

**中间件系统**:

| 中间件 | 功能 |
|--------|------|
| `SubAgentMiddleware` | 子代理调度，通过 `task` 工具分发任务给子代理 |
| `SkillsMiddleware` | 技能系统支持，动态加载 `skills/` 目录下的技能 |
| `SystemTimeMiddleware` | 动态注入系统当前时间到提示词，帮助 Agent 准确回答时间相关问题 |
| `SummarizationMiddleware` | 消息超过20条或token超过10000时自动摘要 |
| `ToolCallingCheckMiddleware` | 检查工具调用是否正确执行，补充缺失的 ToolMessage |
| `HumanInTheLoopMiddleware` | 人工介入，支持 approve/reject 决策 |

**子代理系统** (`subagents/`):

| 子代理 | 功能 |
|--------|------|
| `FileManagerAgent` | 文件管理（读取/写入） |
| `ReseachAgent` | 从多个信息源收集整理信息 |
| `WritingAgent` | 撰写高质量内容 |
| `ReviewAgent` | 审核文本并提供改进建议 |
| `GreetAgent` | 处理问候和基础交互 |
| `UserAgent` | 用户相关操作代理 |

**人工介入模块** (`hitl/`):
- `approve.py`: 审批内容生成，将工具调用转换为用户可读的审批信息

**技能系统** (`agent/skills/`):
- `SkillsMiddleware`: 从 `skills/` 目录加载技能定义，向系统提示词注入可用技能列表
- `load_skill` 工具: 动态加载技能详细描述和参考文档路径

**状态管理** (`memory/`):
- `AppAgentState`: Agent 运行状态，包含消息历史和子代理调用记录
- `AppAgentContext`: Agent 运行时上下文，包含用户信息

### Web 模块 (`src/web/`)

**服务** (`server.py`):
- 基于 FastAPI 的 REST 服务
- 全局异常处理（HTTPException、RequestValidationError、Exception）
- 认证中间件
- 生命周期管理（Postgres 连接初始化/关闭）

**路由** (`api/routes.py`):

| 路由 | 方法 | 功能 |
|------|------|------|
| `/chat/stream` | POST | SSE 流式对话（需认证） |
| `/test/chat/stream` | GET | 测试对话（无需认证） |
| `/health` | GET | 健康检查 |

**认证** (`middleware/auth.py`):
- 基于 session_id 的 Cookie 认证
- 公开路径白名单: `/docs`, `/openapi.json`, `/health`, `/test/chat/stream`

### API 数据模型

#### 请求消息类型 (RequestMsgTypeEnum)
| 枚举值 | 说明 |
|--------|------|
| `NORMAL` | 普通消息 |
| `DECISION` | 决策内容消息 |

#### 响应消息类型 (ResponseMsgTypeEnum)
| 枚举值 | 说明 |
|--------|------|
| `NORMAL` | 普通消息 |
| `PROCESS` | 过程处理消息 |
| `APPROVE` | 审批消息 |
| `ERROR` | 错误消息 |

#### 决策类型 (DecisionType)
| 枚举值 | 说明 |
|--------|------|
| `approve` | 通过 |
| `reject` | 拒绝 |

#### 对话请求 (ChatRequest)
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `msg_type` | `RequestMsgTypeEnum` | 否 | 消息类型，默认 `NORMAL` |
| `content` | `str` | 否 | 对话请求内容 |
| `decision` | `Decision` | 否 | 审批决策内容 |

**校验规则**:
- `msg_type=NORMAL` 时，`content` 不能为空或仅包含空白字符
- `msg_type=DECISION` 时，`decision` 不能为空

#### 对话响应 (ChatResponse[T])
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `msg_id` | `str` | 是 | 消息 ID |
| `msg_type` | `ResponseMsgTypeEnum` | 否 | 消息类型，默认 `NORMAL` |
| `content` | `T` | 否 | 对话响应内容 |
| `approve` | `Approve` | 否 | 审批内容 |
| `created` | `int` | 是 | 创建时间戳 |

#### 审批内容 (Approve)
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `approve_id` | `str` | 是 | 审批 ID |
| `items` | `list[ApproveItem]` | 是 | 审批项 |

#### 审批项 (ApproveItem)
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | `str` | 是 | 审批项名称 |
| `description` | `str` | 是 | 审批项描述 |
| `decisions` | `list[DecisionType]` | 是 | 可选的决策类型列表 |

#### 审批决策 (Decision)
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `decision_id` | `str` | 是 | 决策 ID |
| `items` | `list[DecisionItem]` | 是 | 决策项，和审批内容顺序对应 |

#### 决策项 (DecisionItem)
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `decision_type` | `DecisionType` | 是 | 决策类型 |
| `description` | `str` | 否 | 决策描述，可为空 |


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
- `OPENAI_API_KEY`: 你的 API Key
- `OPENAI_MODEL`: 模型名称
- `OPENAI_BASE_URL`: API 地址

### 3. 启动服务

```bash
uv run src/main.py
```

### 4. 测试

测试对话（无需认证）：
```
GET /test/chat/stream?user_id=test_user&content=你好
```

## 环境配置

项目提供三套环境配置示例文件：
- `.env.example` - 默认配置
- `.env.dev.example` - 开发环境配置示例
- `.env.prod.example` - 生产环境配置示例

### 环境变量说明

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `APP_HOST` | 监听地址 | 127.0.0.1 |
| `APP_PORT` | 监听端口 | 8000 |
| `LOG_LEVEL` | 日志级别 (debug/info/warning/error) | info |
| `LOG_HANDLERS` | 日志处理方式 (console/file) | ["console"] |
| `LOG_FORMAT_TYPE` | 日志格式类型 (text/json) | text |
| `LOG_FILE` | 日志文件路径 | app.log |
| `OPENAI_BASE_URL` | API 地址 | - (必填) |
| `OPENAI_API_KEY` | API Key | - (必填) |
| `OPENAI_MODEL` | 模型名称 | - (必填) |
| `OPENAI_TEMPERATURE` | 温度参数 | 0.7 |
| `OPENAPI_URL` | Swagger 文档路径 (设为 "" 禁用) | /openapi.json |
| `POSTGRES_MEMORY_CONN_STR` | Postgres 连接字符串（用于 checkpointer 和 store） | - |


## 对话流程

```
用户请求 → 认证中间件 → ChatService
                              ↓
                    MainAgent.astream() 异步流式处理
                              ↓
                ┌───────────────┴───────────────┐
                ↓                               ↓
           消息流 (messages)              更新流 (updates)
                ↓                               ↓
           渲染 AIMessageChunk           渲染完整消息/中断
                └───────────────┬───────────────┘
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

## 人工审批流程

某些危险操作（如文件写入）会触发人工审批：

1. 工具调用 → `HumanInTheLoopMiddleware` → `interrupt()` 中断
2. 返回审批请求给前端（`msg_type=APPROVE`）
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
