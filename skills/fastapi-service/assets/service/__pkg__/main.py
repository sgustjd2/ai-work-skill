"""앱 팩토리. lifespan 에서 게이트웨이 클라이언트·프롬프트를 만들고 종료 시 정리한다."""
from __future__ import annotations

import importlib
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.router import api_router
from .core.config import get_settings
from .core.errors import install_error_handlers
from .core.logging import setup_logging
from .core.middleware import RequestContextMiddleware
from .services.llm import LLMClient
from .services.prompts import load_prompts


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(settings.log_level)
    app.state.settings = settings
    app.state.llm = LLMClient(settings)
    app.state.prompts = load_prompts()  # 누락 변수·문법 오류면 기동 실패
    # 옵션 인프라(있으면 초기화). telemetry 는 계측만 하고 상태를 안 둔다.
    for _name in ("telemetry",):
        try:
            mod = importlib.import_module(f"{__package__}.core.{_name}")
        except ImportError:
            continue
        if hasattr(mod, "setup"):
            mod.setup(app)
    try:
        yield
    finally:
        await app.state.llm.aclose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
    app.add_middleware(RequestContextMiddleware)
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    install_error_handlers(app)
    app.include_router(api_router)
    return app


app = create_app()
