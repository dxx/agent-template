from langchain.tools import tool
from datetime import datetime
from langchain.tools import ToolRuntime

from agent.memory import AppAgentContext, AppAgentState

_USER_INFO = {
    "1": {
        "name": "Alice"
    },
    "2": {
        "name": "Tom"
    }
}

@tool
def greet(runtime: ToolRuntime[AppAgentContext, AppAgentState]) -> str:
    """根据当前时间段和用户进行打招呼"""

    print(f"context={runtime.context}")
    sub_agent_calls = runtime.state.get("sub_agent_calls", [])
    print(f"sub_agent_calls={sub_agent_calls}")

    user_info = _USER_INFO.get(runtime.context.user_id, {})
    user_name = user_info.get("name", "")
    
    hour = datetime.now().hour
    if 5 <= hour < 12:
        greeting = "早上好"
    elif 12 <= hour < 14:
        greeting = "中午好"
    elif 14 <= hour < 18:
        greeting = "下午好"
    else:
        greeting = "晚上好"
    return f"{user_name} {greeting}! 请问有什么可以帮你的呢?"
