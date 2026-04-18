# Skills 技能系统

Skills 技能系统允许 Agent 加载和使用专业领域的技能，通过 `SkillsMiddleware` 中间件实现。

## 技能目录结构

```
skills/
└── greet/
    ├── SKILL.md          # 技能定义文件
    └── references/       # 参考文档目录
        └── greet.md
```

## SKILL.md 格式

技能文件使用 YAML frontmatter 格式：

```markdown
---
name: greet
description: 如何和用户打招呼
---

# Greet

技能详细说明...

参考 ./references/greet.md 中的说明进行回复。
```

### Frontmatter 字段

| 字段            | 类型    | 说明   | 限制         |
| ------------- | ----- | ---- | ---------- |
| `name`        | `str` | 技能名称 | 最大 64 字符   |
| `description` | `str` | 技能描述 | 最大 1024 字符 |

## 技能中间件

### SkillsMiddleware

```python
from agent.middleware import SkillsMiddleware

middleware = SkillsMiddleware(
    dirs=["skills"],  # 技能目录列表
    grouped_tools={   # 动态加载的工具分组
        "greet": [greet_tool]
    }
)
```

### 参数说明

| 参数              | 类型                          | 说明                 |
| --------------- | --------------------------- | ------------------ |
| `dirs`          | `list[str]`                 | 技能目录列表，从这些目录加载技能   |
| `grouped_tools` | `dict[str, list[BaseTool]]` | 动态加载的工具分组，key 为技能名 |

### 系统提示词

中间件会自动向系统提示词注入技能列表：

```
## 技能系统
你可以访问技能去处理专业的问题

**可用的技能:**

- **greet**: 如何和用户打招呼
path: /path/to/skills/greet/SKILL.md

**何时使用技能:**
- 当需要更多详细信息去处理用户的问题
- 需要专业的知识或者结构化的流程
- 一个技能提供了复杂任务的处理方式

**如何使用技能:**
使用 `load_skill` 工具加载技能的详细描述
```

## 使用工具

### load_skill

当 Agent 判断需要使用某个技能时，调用 `load_skill` 工具加载技能详情。

```python
load_skill(skill_name: str) -> str
```

### read_source_file

读取技能目录中的参考文件。

```python
read_source_file(file_path: str) -> str
```

## 示例

### GreetAgent

```python
class GreetAgent(SubAgent):
    """带有 Skills 的 Agent"""
    def __init__(self):
        super().__init__()

        # 寻找项目 src 目录
        project_root = Path(__file__).resolve().parent.parent.parent

        skill_dir = project_root.joinpath("skills")

        self._agent = create_agent(
            model=create_chat_model(enable_thinking=False),
            name="greet",
            system_prompt="你是一个专业的招待助手，擅长和用户打招呼。",
            context_schema=AppAgentContext,
            # 子代理需要访问 state 时配置
            state_schema=AppAgentState,
            # 安装 skills 中间件
            middleware=[
                SkillsMiddleware(
                    dirs=[str(skill_dir)],
                    grouped_tools={
                        # 当使用 greet skill 时动态加载 greet 工具
                        "greet": [greet]
                    }
                )
            ]
        )

    def get_name(self) -> str:
        return "greet"

    def get_description(self) -> str:
        return "擅长和用户打招呼"
```

### 创建技能

在 `skills/greet/` 目录下创建 `SKILL.md`：

```markdown
---
name: greet
description: 如何和用户打招呼
---

# Greet

用户打招呼的时候参考 ./references/greet.md 中的说明进行回复。
```

创建参考文件 `skills/greet/references/greet.md`：

```markdown
# 打招呼方式

## 简单回复

用户询问方式和回复:

- **你好**: 你好啊

## 用工具回复

以上情况不满足的时候，使用 `greet` 工具和用户进行打招呼。
```

### 接口访问

请求：

```bash
### 访问技能
POST http://localhost:8000/chat/stream
Content-Type: application/json
Connection: keep-alive
user-token: user_123
chat-id: chat_782e77c0-ddb6-45a7-b8ae-5c16a3f51916

{
  "content": "我叫 Alice，你叫什么。请使用 greet 技能回复"
}
```

返回： 

```
data: {"msg_id":"lc_run--019d9f61-3417-7e52-95d2-eb0fc23c0836","msg_type":"process","content":"调用: task","approve":null,"created":1776495443195}

data: {"msg_id":"lc_run--019d9f61-3d00-76c1-8557-6bfea3ff0cc6","msg_type":"process","content":"调用: load_skill","approve":null,"created":1776495445123}

data: {"msg_id":"17dd44c1-d155-40f2-8d01-98d0b2105659","msg_type":"process","content":"load_skill 执行结果: # Greet\n\n用户打招呼的时候参考 ./references/greet.md 中的说明进行回复。","approve":null,"created":1776495445125}

data: {"msg_id":"lc_run--019d9f61-4489-7a72-ab22-3af3857e8034","msg_type":"process","content":"调用: read_source_file","approve":null,"created":1776495446210}

data: {"msg_id":"1990a3b2-cf82-4a67-8742-5317ea40786d","msg_type":"process","content":"read_source_file 执行结果: # 打招呼方式\n\n## 简单回复\n\n用户询问方式和回复:\n\n- **你好**: 你好啊\n\n## 用工具回复\n\n以上情况不满足的时候，使用 `greet` 工具和用户进行打招呼。\n","approve":null,"created":1776495446227}

data: {"msg_id":"lc_run--019d9f61-48d6-7031-b1a9-32dd614f0f94","msg_type":"process","content":"调用: greet","approve":null,"created":1776495447230}

data: {"msg_id":"709b8919-d54d-48b7-a18b-c4075abfe276","msg_type":"process","content":"greet 执行结果: Alice 下午好! 请问有什么可以帮你的呢?","approve":null,"created":1776495447232}

data: {"msg_id":"0c77c0c9-a6b1-4494-b8b0-cd6e5868ca1e","msg_type":"process","content":"task 执行结果: Alice 下午好! 我叫招待助手，很高兴认识你！请问有什么可以帮你的呢?","approve":null,"created":1776495448135}

data: {"msg_id":"lc_run--019d9f61-504b-7821-9876-ca7f85d54ee5","msg_type":"normal","content":"Alice","approve":null,"created":1776495448779}

data: {"msg_id":"lc_run--019d9f61-504b-7821-9876-ca7f85d54ee5","msg_type":"normal","content":" ","approve":null,"created":1776495448861}

data: {"msg_id":"lc_run--019d9f61-504b-7821-9876-ca7f85d54ee5","msg_type":"normal","content":"下午","approve":null,"created":1776495448861}

data: {"msg_id":"lc_run--019d9f61-504b-7821-9876-ca7f85d54ee5","msg_type":"normal","content":"好","approve":null,"created":1776495448861}

...
```

## 工作流程

1. **技能发现**：Agent 根据用户问题判断需要使用哪个技能
2. **加载技能**：Agent 调用 `load_skill` 工具获取技能详情
3. **执行技能**：按照技能文档中的指引执行相应操作
4. **读取参考**：如需读取参考文件，使用 `read_source_file` 工具

## 动态工具加载

当 Agent 加载某个技能后，`SkillsMiddleware` 会自动将该技能对应的工具添加到模型调用中：

```python
grouped_tools={
    "greet": [greet_tool],  # 加载 greet 技能后，greet_tool 会被加入工具列表
    "search": [search_tool]
}
```

## 注意

为了安全性考虑，该项目运行在服务端，skills 技能系统不支持执行脚本。
