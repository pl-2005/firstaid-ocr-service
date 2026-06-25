from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException

from app.api.errors import http_exception_handler
from app.api.routes import router
from app.core.config import settings
from app.services.ocr import ocr_engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    if settings.auto_load:
        ocr_engine.load()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Local PaddleOCR service for FIRST-AID.",
        lifespan=lifespan,
    )
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.include_router(router)

    return app


app = create_app()
