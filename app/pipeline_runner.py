import os
import sys
import logging
import traceback
from io import StringIO
from datetime import datetime

from src import config_loader
from src import utils
from src import link_parser

logger = logging.getLogger("pipeline_runner")


class PipelineRunner:
    def __init__(self):
        self.logs: list[str] = []
        self._setup_log_capture()

    def _setup_log_capture(self):
        self._log_stream = StringIO()
        self._stream_handler = logging.StreamHandler(self._log_stream)
        self._stream_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S",
        )
        self._stream_handler.setFormatter(formatter)
        root = logging.getLogger()
        root.addHandler(self._stream_handler)
        root.setLevel(logging.INFO)

    def flush_logs(self) -> list[str]:
        self._log_stream.seek(0)
        lines = self._log_stream.read().splitlines()
        self._log_stream.seek(0)
        self._log_stream.truncate(0)
        return lines

    def _ensure_handler(self):
        root = logging.getLogger()
        if self._stream_handler not in root.handlers:
            root.addHandler(self._stream_handler)

    def run_single(self, url: str, config: dict, mode: str = "basic") -> dict:
        from main import process_single_video

        task_config = {"mode": mode}
        project_root = config_loader.get_project_root()

        log_dir = config_loader.resolve_path(config, "log_dir")
        utils.setup_logging(log_dir, f"web_{mode}")

        self._ensure_handler()

        self.flush_logs()

        success = process_single_video(url, task_config, config, 1)

        new_logs = self.flush_logs()

        processed_file = os.path.join(project_root, "processed.json")
        processed = utils.load_json(processed_file, [])

        output_dir = ""
        title = ""
        for item in reversed(processed):
            if item.get("url") == url and item.get("mode") == mode:
                output_dir = item.get("output_dir", "")
                title = item.get("title", "")
                break

        return {
            "success": success,
            "url": url,
            "title": title,
            "output_dir": output_dir,
            "mode": mode,
            "logs": new_logs,
            "completed_at": datetime.now().isoformat(),
        }

    def run_batch(self, urls: list[str], config: dict, mode: str = "basic") -> list[dict]:
        results = []
        for idx, url in enumerate(urls):
            result = self.run_single(url, config, mode)
            results.append(result)
        return results

    def parse_url_text(self, text: str, bilibili_only: bool = True) -> list[str]:
        seen = set()
        urls = []
        lines = text.strip().split("\n")
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if bilibili_only:
                found = link_parser.extract_bilibili_urls(line)
            else:
                found = link_parser.extract_all_urls(line)
            for u in found:
                if u not in seen:
                    seen.add(u)
                    urls.append(u)
        return urls

    def run_single_with_progress(self, url: str, config: dict, mode: str = "basic"):
        result = self.run_single(url, config, mode)
        return result

    def cleanup(self):
        root = logging.getLogger()
        if self._stream_handler in root.handlers:
            root.removeHandler(self._stream_handler)
