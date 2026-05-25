from pydantic import BaseModel
from typing import Optional, Any, Generic, TypeVar
from enum import Enum

T = TypeVar("T")


class TaskMode(str, Enum):
    basic = "basic"
    with_images = "with_images"


class TaskStatus(str, Enum):
    pending = "pending"
    downloading = "downloading"
    transcribing = "transcribing"
    cleaning = "cleaning"
    summarizing = "summarizing"
    mindmap = "mindmap"
    screenshot = "screenshot"
    completed = "completed"
    failed = "failed"


class TaskCreateRequest(BaseModel):
    urls: list[str]
    mode: TaskMode = TaskMode.basic


class TaskInfo(BaseModel):
    task_id: str
    url: str
    title: str = ""
    mode: TaskMode
    status: TaskStatus = TaskStatus.pending
    progress: float = 0.0
    stage_message: str = ""
    output_dir: str = ""
    error_message: str = ""
    created_at: str = ""
    completed_at: str = ""


class ApiResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "success"
    data: Optional[T] = None


class ConfigUpdateRequest(BaseModel):
    whisper_model: Optional[str] = None
    whisper_language: Optional[str] = None
    whisper_device: Optional[str] = None
    whisper_compute_type: Optional[str] = None
    deepseek_model: Optional[str] = None
    deepseek_base_url: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    screenshot_enabled: Optional[bool] = None
    screenshot_strategy: Optional[str] = None
    screenshot_min_interval_seconds: Optional[float] = None
    screenshot_max_avg_per_minute: Optional[float] = None
    screenshot_difference_threshold: Optional[float] = None


# --- Config display models (for GET /api/config) ---

class WhisperConfig(BaseModel):
    model: str
    language: str
    device: str
    compute_type: str = "auto"


class DeepseekConfig(BaseModel):
    model: str
    base_url: str
    has_api_key: bool = False
    max_chunk_minutes: int = 12


class ScreenshotConfig(BaseModel):
    enabled: bool = False
    strategy: str = "learning"
    min_interval_seconds: float = 3.0
    max_avg_per_minute: float = 6.0
    max_images_per_unit: int = 2
    difference_threshold: float = 0.85


class ProjectConfig(BaseModel):
    name: str
    output_dir: str
    log_dir: str
    temp_dir: str
    download_dir: str


class ConfigDisplay(BaseModel):
    project: ProjectConfig
    whisper: WhisperConfig
    deepseek: DeepseekConfig
    screenshot: ScreenshotConfig


# --- API key check response ---

class ApiKeyStatus(BaseModel):
    valid: bool
    message: str = ""


# --- Video metadata (from yt-dlp) ---

class VideoMetadata(BaseModel):
    title: str = ""
    duration: float = 0.0
    uploader: str = ""
    upload_date: str = ""
    description: str = ""
    webpage_url: str = ""
