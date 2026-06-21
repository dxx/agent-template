# 配置说明

项目使用 `pydantic-settings` 管理配置。配置定义位于 `src/config/settings.py`，示例配置位于项目根目录 `.env.example`。

## 配置文件

项目支持两个环境配置文件：

```text
.env
.env.{APP_ENV}
```

例如：

```text
.env
.env.dev
.env.prod
```

可增加额外的环境配置，配置文件名格式: `.env.环境名称`，然后在 `src/config/settings.py` 中增加对应的代码。

配置文件路径会从 `src/config/settings.py` 向上查找到项目根目录：

```python
path = Path(__file__).resolve().parent.parent.parent
env_path = path.joinpath(f".env.{_app_env}")
default_env_path = path.joinpath(".env")
```

`Settings` 会按以下顺序加载 env 文件：

```python
env_file=[default_env_path, env_path]
```

因此通常可以把公共配置放在 `.env`，把不同环境的覆盖配置放在 `.env.dev` 或 `.env.prod`。

## APP_ENV

`APP_ENV` 用于决定当前运行环境。

支持值：

| 值 | 说明 |
| --- | --- |
| `dev` | 开发环境。 |
| `prod` | 生产环境。 |

如果没有设置 `APP_ENV`，系统会默认设置为 `dev`，如果 `APP_ENV` 不是 `dev` 或 `prod`，应用启动时会抛出异常。

## 快速开始

复制 `.env.example` 中的配置到 `.env` 或 `.env.dev`，然后按实际环境修改。

示例：

```env
APP_HOST=127.0.0.1
APP_PORT=8000

LOG_LEVEL=info
LOG_HANDLERS=["console"]
LOG_FORMAT_TYPE=text
LOG_FILE=logs/app.log

CORS_ALLOW_ORIGINS=["*"]
CORS_ALLOW_CREDENTIALS=false

OPENAI_BASE_URL=
OPENAI_PROVIDER=bailian
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.7

POSTGRES_MEMORY_CONN_STR=postgresql://用户名:密码@IP:PORT/数据库名
```

## 配置读取

项目通过 `get_settings()` 获取配置：

```python
from config import get_settings

settings = get_settings()
```

`get_settings()` 使用 `lru_cache` 缓存配置对象，避免重复解析环境变量和配置文件。

```python
@lru_cache
def get_settings() -> Settings:
    return Settings(app_env=_app_env)
```

如需重新加载配置，可以调用：

```python
from config.settings import reload_settings

settings = reload_settings()
```

## 应用配置

| 环境变量 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `APP_ENV` | `str` | `dev` | 应用运行环境，支持 `dev`、`prod`。 |
| `APP_HOST` | `str` | `127.0.0.1` | 应用监听地址。 |
| `APP_PORT` | `int` | `8000` | 应用监听端口。 |
| `OPENAPI_URL` | `str` | `/openapi.json` | OpenAPI schema 地址。 |

## 日志配置

| 环境变量 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `LOG_LEVEL` | `str` | `info` | 日志级别，例如 `debug`、`info`、`warning`、`error`。 |
| `LOG_HANDLERS` | `list[str]` | `["console"]` | 日志输出方式，支持 `console`、`file`。 |
| `LOG_FORMAT_TYPE` | `str` | `text` | 日志格式，支持 `text`、`json`。 |
| `LOG_FILE` | `str` | `logs/app.log` | 文件日志路径，仅当 `LOG_HANDLERS` 包含 `file` 时使用。 |

示例：

```env
LOG_LEVEL=debug
LOG_HANDLERS=["console", "file"]
LOG_FORMAT_TYPE=json
LOG_FILE=logs/app.log
```

说明：

- `console` 会输出到控制台
- `file` 会输出到 `LOG_FILE` 指定的文件
- 使用文件日志时，项目会自动创建日志目录

## CORS 配置

| 环境变量 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `CORS_ALLOW_ORIGINS` | `list[str]` | `[]` | 允许访问的来源列表。 |
| `CORS_ALLOW_CREDENTIALS` | `bool` | `false` | 是否允许跨域请求携带凭证。 |

示例：

```env
CORS_ALLOW_ORIGINS=["http://localhost:3000", "https://example.com"]
CORS_ALLOW_CREDENTIALS=true
```

开发环境如果允许所有来源，可以使用：

```env
CORS_ALLOW_ORIGINS=["*"]
```

这些配置会传给 FastAPI `CORSMiddleware`。

## 模型配置

项目通过 OpenAI 兼容接口创建聊天模型。

| 环境变量 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `OPENAI_PROVIDER` | `str` | 无 | 模型提供商。 |
| `OPENAI_BASE_URL` | `str` | 无 | OpenAI 兼容 API 地址，会自动补充 `/chat/completions` |
| `OPENAI_API_KEY` | `str` | 无 | API Key。可引用环境变量，如 ${API_KEY} |
| `OPENAI_MODEL` | `str` | 无 | 模型名称。 |
| `OPENAI_TEMPERATURE` | `float` | `0.7` | 模型温度。 |

当前支持的 `OPENAI_PROVIDER`：

| 值 | 说明 |
| --- | --- |
| `bailian` | 阿里云百炼兼容接口。 |
| `volcengine` | 火山引擎兼容接口。 |
| `deepseek` | DeepSeek 兼容接口。 |
| `bigmodel` | 智谱 BigModel 兼容接口。 |
| `minimax` | MiniMax 兼容接口。 |

模型创建逻辑位于 `src/agent/llm/model.py`：

```python
init_chat_model(
    model=settings.openai_model,
    model_provider="openai",
    base_url=settings.openai_base_url,
    api_key=SecretStr(settings.openai_api_key) if settings.openai_api_key else None,
    temperature=settings.openai_temperature,
    extra_body=_build_extra_body(settings.openai_provider, enable_thinking),
)
```

不同提供商会生成不同的 `extra_body`。

## Postgres 记忆配置

| 环境变量 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `POSTGRES_MEMORY_CONN_STR` | `str` | 无 | Postgres 连接字符串，用于 checkpointer 和 store。 |

示例：

```env
POSTGRES_MEMORY_CONN_STR=postgresql://user:password@127.0.0.1:5432/agent
```

## 类型写法

`.env` 中的列表和布尔值需要符合 Pydantic 可解析格式。

列表：

```env
LOG_HANDLERS=["console", "file"]
CORS_ALLOW_ORIGINS=["*"]
```

布尔值：

```env
CORS_ALLOW_CREDENTIALS=false
```

数字：

```env
APP_PORT=8000
OPENAI_TEMPERATURE=0.7
```

## 必填配置

以下配置没有默认值，通常需要在 `.env` 或 `.env.{APP_ENV}` 中提供：

| 环境变量 | 说明 |
| --- | --- |
| `OPENAI_PROVIDER` | 模型提供商。 |
| `OPENAI_BASE_URL` | 模型 API 地址。 |
| `OPENAI_API_KEY` | 模型 API Key。 |
| `OPENAI_MODEL` | 模型名称。 |
| `POSTGRES_MEMORY_CONN_STR` | Postgres 记忆连接字符串。 |

如果缺少这些配置，`Settings` 初始化时会校验失败。

## 最小配置示例

```env
APP_ENV=dev

OPENAI_PROVIDER=bailian
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=qwen-plus

POSTGRES_MEMORY_CONN_STR=postgresql://user:password@127.0.0.1:5432/agent
```

## 注意事项

- `.env.example` 是示例文件，不应填写真实密钥
- 真实密钥应放在本地 `.env`、`.env.dev` 或部署平台的环境变量中
- `APP_ENV` 会影响加载的环境文件名称
- `.env.{APP_ENV}` 可以覆盖 `.env` 中的同名配置
- `get_settings()` 有缓存，运行时修改环境变量后需要调用 `reload_settings()` 才能重新读取
- `OPENAI_PROVIDER` 会影响不同模型提供商的额外请求参数
