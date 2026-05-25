import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, TypeAdapter

from web.routes import tasks, outputs, config, ws, media
from web.models import (
    ApiResponse, TaskInfo, TaskStatus,
    ConfigDisplay, WhisperConfig, DeepseekConfig, ScreenshotConfig, ProjectConfig,
    ApiKeyStatus, VideoMetadata,
)


def _fix_refs(obj):
    """Recursively replace `#/$defs/X` references with `#/components/schemas/X`
    so openapi-typescript can resolve them."""
    if isinstance(obj, dict):
        if "$ref" in obj and isinstance(obj["$ref"], str):
            obj["$ref"] = obj["$ref"].replace("#/$defs/", "#/components/schemas/")
        for key, value in obj.items():
            _fix_refs(value)
    elif isinstance(obj, list):
        for item in obj:
            _fix_refs(item)


def _inject_openapi_schemas(app: FastAPI):
    """Inject model schemas that aren't referenced by response_model annotations
    so openapi-typescript can discover them for the frontend type contract."""

    models: list[type[BaseModel]] = [
        TaskInfo,
        ConfigDisplay, WhisperConfig, DeepseekConfig, ScreenshotConfig, ProjectConfig,
        ApiKeyStatus, VideoMetadata,
    ]

    original_openapi = app.openapi

    def custom_openapi():
        if app.openapi_schema is not None:
            return app.openapi_schema

        schema = original_openapi()

        for model in models:
            json_schema = model.model_json_schema()
            _fix_refs(json_schema)
            schema["components"]["schemas"][json_schema["title"]] = json_schema

        # Inject TaskStatus enum (str, Enum doesn't have model_json_schema)
        ts_schema = TypeAdapter(TaskStatus).json_schema()
        ts_schema["title"] = "TaskStatus"
        _fix_refs(ts_schema)
        schema["components"]["schemas"]["TaskStatus"] = ts_schema

        app.openapi_schema = schema
        return schema

    app.openapi = custom_openapi


def create_app() -> FastAPI:
    app = FastAPI(
        title="Bili Video Notes API",
        description="B站视频自动笔记生成工作流 Web API",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(tasks.router)
    app.include_router(outputs.router)
    app.include_router(config.router)
    app.include_router(ws.router)
    app.include_router(media.router)

    @app.get("/api/status", response_model=ApiResponse)
    def health_check():
        return ApiResponse(data={"status": "ok"}).model_dump()

    _inject_openapi_schemas(app)

    frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
    if os.path.exists(frontend_dist):
        app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")

    return app
