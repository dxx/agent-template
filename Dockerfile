# 基于 Debian 12 系统的 Python 3.12 + UV 环境
FROM m.daocloud.io/docker.io/astral/uv:0.9-python3.12-bookworm-slim

# 使用上面的镜像，构建比下面快
# 基于 Debian 12 系统的 Python 3.12 环境
# FROM m.daocloud.io/docker.io/library/python:3.12-slim-bookworm
# 安装 uv 到 /bin/ 目录中
# COPY --from=m.daocloud.io/docker.io/astral/uv:0.11.2 /uv /uvx /bin/

# 工作目录
WORKDIR /app

# 由于是挂载卷，因此从缓存中复制而非链接
ENV UV_LINK_MODE=copy

# 省略开发依赖项
ENV UV_NO_DEV=1

# 安装依赖
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

# 复制项目到镜像中
COPY . /app

# 同步项目依赖
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

# 将执行环境放到 PATH 之前
ENV PATH="/app/.venv/bin:$PATH"

# 重置 entrypoint, 不要调用 `uv`
ENTRYPOINT []

# 监听任意地址
ENV APP_HOST=0.0.0.0

CMD ["uv", "run", "python", "src/main.py"]
