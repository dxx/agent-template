from langchain.tools import tool
from langchain.tools import ToolRuntime
from pydantic import BaseModel, Field

from agent.memory import AppAgentContext, AppAgentState

class UserInfo(BaseModel):
    """用户信息"""
    name: str = Field(description="用户名称")
    email: str = Field(description="用户邮箱")
    hobby: list[str] = Field(default=[], description="爱好")

# 命名空间
namespace = ("user",)

@tool
def save_user_info(user_info: UserInfo, runtime: ToolRuntime[AppAgentContext, AppAgentState]) -> str:
    """保存用户信息"""
    store = runtime.store
    user_id = runtime.context.user_id
    # 保存数据，数据类型为字典 (namespace, key, data)
    store.put(namespace, user_id, user_info.model_dump())
    return "保存用户信息成功"

@tool
def get_user_info(runtime: ToolRuntime[AppAgentContext, AppAgentState]) -> str:
    """获取用户信息"""
    store = runtime.store
    user_id = runtime.context.user_id
    item = store.get(namespace, user_id)
    user_info = item.value
    # 字典类型
    print(type(user_info))
    return str(user_info)
