"""Store namespace 统一前缀。

多个项目共用同一个存储实例时，通过 namespace 前缀做逻辑隔离，
避免 Postgres 的 store 表或 Redis 的 store:* 键互相串号。

注意：前缀不要包含 Redis 的 ``:`` 或 Postgres namespace 的 ``.`` 分隔符。
"""

PREFIX = "agent_template"
"""项目唯一标识，用于给 store namespace 和 thread_id 加前缀。"""


def ns(*parts: str) -> tuple[str, ...]:
    """构造带前缀的 store namespace。"""

    return (PREFIX, *parts)
