# scaffold: with-otel
"""OpenTelemetry 계측. OTLP 엔드포인트는 환경변수(OTEL_EXPORTER_OTLP_ENDPOINT)."""
from __future__ import annotations

from fastapi import FastAPI


def setup(app: FastAPI) -> None:
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    except ImportError:
        return
    FastAPIInstrumentor.instrument_app(app)
    HTTPXClientInstrumentor().instrument()
