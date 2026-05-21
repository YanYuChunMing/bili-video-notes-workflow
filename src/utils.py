import os
import re
import json
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


def setup_logging(log_dir: str, task_name: str = "workflow") -> logging.Logger:
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"{task_name}_{timestamp}.log")

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_fmt)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_fmt = logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
    console_handler.setFormatter(console_fmt)
    root_logger.addHandler(console_handler)

    return root_logger


def sanitize_filename(name: str) -> str:
    illegal_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(illegal_chars, "_", name)
    sanitized = sanitized.strip().strip(".")
    if not sanitized:
        sanitized = "untitled"
    max_len = 120
    if len(sanitized) > max_len:
        sanitized = sanitized[:max_len]
    return sanitized


def ensure_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path


def generate_output_dirname(base_dir: str, index: int, title: str) -> str:
    safe_title = sanitize_filename(title)
    dirname = f"{index:03d}_{safe_title}"
    full_path = os.path.join(base_dir, dirname)
    os.makedirs(full_path, exist_ok=True)
    return full_path


def load_json(filepath: str, default=None):
    if default is None:
        default = []
    if not os.path.exists(filepath):
        return default
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default


def save_json(filepath: str, data):
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def seconds_to_timestamp(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def timestamp_to_filename(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}_{minutes:02d}_{secs:02d}"


def read_text_file(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def write_text_file(filepath: str, content: str):
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


def is_url_already_processed(url: str, processed_file: str, mode: str = "") -> bool:
    processed = load_json(processed_file, [])
    if mode:
        return any(item.get("url") == url and item.get("mode") == mode for item in processed)
    return any(item.get("url") == url for item in processed)


def mark_url_processed(url: str, title: str, output_dir: str, mode: str, processed_file: str):
    processed = load_json(processed_file, [])
    processed.append(
        {
            "url": url,
            "title": title,
            "output_dir": output_dir,
            "mode": mode,
            "processed_at": datetime.now().isoformat(),
        }
    )
    save_json(processed_file, processed)


def mark_url_failed(url: str, mode: str, error: str, failed_file: str):
    failed = load_json(failed_file, [])
    failed.append(
        {
            "url": url,
            "mode": mode,
            "error": str(error),
            "failed_at": datetime.now().isoformat(),
        }
    )
    save_json(failed_file, failed)
