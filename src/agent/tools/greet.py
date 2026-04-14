from langchain.tools import tool
from datetime import datetime
from langchain.tools import ToolRuntime

from agent.memory import AppAgentContext, AppAgentState
from agent.tools.user import namespace

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
    print(f"store={runtime.store}")

    user_id = runtime.context.user_id
    user_name = ""
    if runtime.store:
        # 从 Store 中获取信息
        item = runtime.store.get(namespace, user_id)
        if item and item.value:
            user_info = item.value
            print(f"user_info={user_info}")
            user_name = user_info["name"]
    if not user_name:
        user_info = _USER_INFO.get(user_id, {})
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
