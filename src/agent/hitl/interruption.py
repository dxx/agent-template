from typing import TypeAlias, Protocol
from langchain.agents.middleware.human_in_the_loop import (
    DecisionType,
    ActionRequest,
    ReviewConfig,
    HITLRequest,
    HITLResponse,
    ApproveDecision,
    RejectDecision,
)
from langgraph.types import interrupt


HITLDecision: TypeAlias = ApproveDecision | RejectDecision


class _ActionDescriptionFactory(Protocol):
    """为动作生成描述的 Callable"""

    def __call__(
        self, name: str, args: dict
    ) -> str:
        """为动作生成描述。"""
        ...


def hitl_interrupt(
    action_name: str,
    allowed_decisions: list[DecisionType],
    args: dict,
    description: str | _ActionDescriptionFactory | None = None,
) -> HITLDecision:
    """人工介入中断。
    interrupt 执行的接收内容和返回内容与 HumanInTheLoopMiddleware 的一致。

    Args:
        action_name: 需要人工审批的动作名称（如工具名）。
        allowed_decisions: 该动作允许的人工决策类型，可选 `approve` / `reject`。
        args: 动作的参数，会原样放入 `ActionRequest.args`。
        description: 展示给审批人的动作描述，可选。

            - 传入字符串时直接使用
            - 传入 Callable 时调用 `description(action_name, args)` 动态生成
            - 缺省时使用默认格式：`Tool execution requires approval\n\nTool: {action_name}\nArgs: {args}`

    Returns:

    approve 时: ApproveDecision {'type': 'approve'}

    reject 时: RejectDecision {'type': 'reject', 'message': '用户拒绝了 `write_file` 的执行，工具未被执行。'}

    LangChain 的 Interrupt 返回示例:

    value = {
        'action_requests': [{
            'name': 'write_file',
            'args': {
                'file_path': 'hello.txt',
                'content': 'hello'
            },
            'description': '写入文件需要审批'
        }],
        'review_configs': [{
            'action_name': 'write_file',
            'allowed_decisions': ['approve', 'reject']
        }]
    },
    id = 'f96ef5b2139198600bd7c58db3248380'
    """

    if callable(description):
        description_value = description(action_name, args)
    elif description is not None:
        description_value = description
    else:
        description_value = (
            f"Tool execution requires approval\n\nTool: {action_name}\nArgs: {args}"
        )

    hitl_request = HITLRequest(
        action_requests=[
            ActionRequest(
                name=action_name,
                args=args,
                description=description_value,
            )
        ],
        review_configs=[
            ReviewConfig(
                action_name=action_name,
                allowed_decisions=list(allowed_decisions),
            )
        ],
    )

    response: HITLResponse = interrupt(hitl_request)
    decisions = response["decisions"]

    if len(decisions) != 1:
        msg = (
            f"Number of human decisions ({len(decisions)}) does not match "
            f"number of interrupted actions (1)."
        )
        raise ValueError(msg)

    decision = decisions[0]
    decision_type = decision["type"]

    if decision_type == "approve" and "approve" in allowed_decisions:
        return {"type": "approve"}

    if decision_type == "reject" and "reject" in allowed_decisions:
        message = decision.get("message") or (
            f"用户拒绝了 `{action_name}` 的执行，工具未被执行。"
        )
        return {"type": "reject", "message": message}

    msg = (
        f"Unexpected human decision: {decision}. "
        f"Decision type '{decision_type}' "
        f"is not allowed for action '{action_name}'. "
        f"Expected one of {allowed_decisions} based on the action's configuration."
    )
    raise ValueError(msg)
