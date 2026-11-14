from contextlib import asynccontextmanager
from typing import AsyncGenerator

from opentelemetry import propagate, trace
from opentelemetry.context.context import Context
from opentelemetry.trace import ProxyTracerProvider, SpanKind, Status, StatusCode
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.id_generator import RandomIdGenerator
from opentelemetry.semconv.attributes.http_attributes import (
    HTTP_REQUEST_METHOD,
    HTTP_RESPONSE_STATUS_CODE,
)
from opentelemetry.semconv.attributes.url_attributes import URL_PATH
from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send


OTEL_TRACE_ID_KEY = "otel-trace-id"
"""OTel 追踪 ID"""

_TRACER_NAME = "agent-tracing"
_SPAN_NAME = "http.request"

_id_generator = RandomIdGenerator()


def init_tracing() -> None:
    """初始化全局 TracerProvider"""

    provider = trace.get_tracer_provider()
    if isinstance(provider, ProxyTracerProvider):
        trace.set_tracer_provider(TracerProvider())


def new_trace_id() -> str:
    """生成新的 trace id"""

    return trace.format_trace_id(_id_generator.generate_trace_id())


def get_current_trace_id() -> str | None:
    """获取当前上下文中的 trace id，无有效 span 时返回 None"""

    span_context = trace.get_current_span().get_span_context()
    if not span_context.is_valid:
        return None

    return trace.format_trace_id(span_context.trace_id)


def build_trace_header(*trace_keys: str) -> dict[str, str]:
    """构造下游请求头，包含标准 traceparent 和自定义追踪字段

    位置参数为额外的 header key，值统一使用当前 trace id
    """

    trace_id = get_current_trace_id()
    if not trace_id:
        return {}

    header: dict[str, str] = {}
    propagate.inject(header)

    for key in trace_keys:
        if key == "traceparent":
            # 避免覆盖标准的 traceparent
            continue
        header[key] = trace_id

    return header


@asynccontextmanager
async def start_span(
    span_name: str,
    context: Context | None = None,
    trace_id: str | None = None,
    kind: SpanKind = SpanKind.INTERNAL,
) -> AsyncGenerator[trace.Span, None]:
    """开启一个 span，传入 context 或 trace_id 时延续上游链路"""

    tracer = trace.get_tracer(_TRACER_NAME)

    if context is None and trace_id:
        parent = _build_remote_context(trace_id)
        if parent is not None:
            context = trace.set_span_in_context(trace.NonRecordingSpan(parent))

    with tracer.start_as_current_span(span_name, context=context, kind=kind) as span:
        yield span


class TracingMiddleware:
    """提取请求头中的上游追踪上下文，创建服务端 span，
    并把 trace id 写入响应头
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        carrier = {
            key.decode("latin-1").lower(): value.decode("latin-1")
            for key, value in scope.get("headers", [])
        }

        # 标准 traceparent 优先，缺失时回退到自定义的 trace id 请求头
        context = propagate.extract(carrier)
        trace_id: str | None = None
        if not trace.get_current_span(context).get_span_context().is_valid:
            context = None
            trace_id = carrier.get(OTEL_TRACE_ID_KEY) or None

        method = scope.get("method", "")
        path = scope.get("path", "")
        status_code = 0

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                headers = MutableHeaders(scope=message)
                headers[OTEL_TRACE_ID_KEY] = span_trace_id
            await send(message)

        async with start_span(
            _SPAN_NAME,
            context=context,
            trace_id=trace_id,
            kind=SpanKind.SERVER,
        ) as span:
            span.set_attribute(HTTP_REQUEST_METHOD, method)
            span.set_attribute(URL_PATH, path)

            span_trace_id = trace.format_trace_id(span.get_span_context().trace_id)

            try:
                await self.app(scope, receive, send_wrapper)
            except Exception as exc:
                span.set_status(Status(StatusCode.ERROR, str(exc)))
                span.record_exception(exc)
                raise

            if status_code:
                span.set_attribute(HTTP_RESPONSE_STATUS_CODE, status_code)


def _build_remote_context(trace_id: str) -> trace.SpanContext | None:
    try:
        trace_id_value = int(trace_id, 16)
    except ValueError:
        return None

    if trace_id_value <= 0 or trace_id_value >= 2**128:
        return None

    return trace.SpanContext(
        trace_id=trace_id_value,
        span_id=_id_generator.generate_span_id(),
        is_remote=True,
        trace_flags=trace.TraceFlags(trace.TraceFlags.SAMPLED),
    )
