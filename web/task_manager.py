import os
import uuid
import shutil
import threading
import logging
from datetime import datetime
from typing import Optional

from web.models import TaskInfo, TaskStatus

logger = logging.getLogger("web.task_manager")

_tasks: dict[str, TaskInfo] = {}
_lock = threading.Lock()


def create_task(url: str, mode: str) -> TaskInfo:
    task_id = uuid.uuid4().hex[:12]
    now = datetime.now().isoformat()
    task = TaskInfo(
        task_id=task_id,
        url=url,
        mode=mode,
        status=TaskStatus.pending,
        created_at=now,
    )
    with _lock:
        _tasks[task_id] = task
    return task


def get_task(task_id: str) -> Optional[TaskInfo]:
    with _lock:
        return _tasks.get(task_id)


def get_all_tasks() -> list[TaskInfo]:
    with _lock:
        return list(_tasks.values())


def update_task(task_id: str, **kwargs):
    with _lock:
        task = _tasks.get(task_id)
        if task is None:
            return
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)


def delete_task(task_id: str) -> bool:
    with _lock:
        task = _tasks.get(task_id)
        if task is None:
            return False
        output_dir = task.output_dir
        del _tasks[task_id]

    if output_dir and os.path.isdir(output_dir):
        try:
            shutil.rmtree(output_dir)
            logger.info(f"已删除任务产物目录: {output_dir}")
        except Exception as e:
            logger.warning(f"删除产物目录失败: {e}")

    return True


def run_task(task_id: str, url: str, mode: str, config: dict):
    from src import config_loader
    from src import utils

    def progress_callback(stage: str, message: str, progress: float):
        update_task(
            task_id,
            status=TaskStatus(stage) if stage in TaskStatus._value2member_map_ else TaskStatus.downloading,
            stage_message=message,
            progress=progress,
        )

    try:
        update_task(
            task_id,
            status=TaskStatus.downloading,
            stage_message="开始下载...",
        )

        from main import process_single_video

        task_config = {"mode": mode}
        success = process_single_video(
            url=url,
            task_config=task_config,
            config=config,
            index=1,
            progress_callback=progress_callback,
        )

        if success:
            from src import config_loader
            project_root = config_loader.get_project_root()
            processed_file = os.path.join(project_root, "processed.json")
            processed_list = utils.load_json(processed_file, [])
            matched = None
            for item in processed_list:
                if item.get("url") == url and item.get("mode") == mode:
                    matched = item
                    break
            output_dir = matched.get("output_dir", "") if matched else ""
            title = matched.get("title", "") if matched else ""

            update_task(
                task_id,
                status=TaskStatus.completed,
                progress=1.0,
                stage_message="处理完成",
                output_dir=output_dir,
                title=title,
                completed_at=datetime.now().isoformat(),
            )
        else:
            update_task(
                task_id,
                status=TaskStatus.failed,
                stage_message="处理失败",
                completed_at=datetime.now().isoformat(),
            )

    except Exception as e:
        logger.error(f"任务 {task_id} 执行异常: {e}")
        update_task(
            task_id,
            status=TaskStatus.failed,
            error_message=str(e),
            stage_message="处理异常",
            completed_at=datetime.now().isoformat(),
        )

        try:
            from src import config_loader, utils
            project_root = config_loader.get_project_root()
            failed_file = os.path.join(project_root, "failed.json")
            utils.mark_url_failed(url, mode, str(e), failed_file)
        except Exception:
            pass


def start_task(task_id: str, url: str, mode: str, config: dict):
    thread = threading.Thread(
        target=run_task,
        args=(task_id, url, mode, config),
        daemon=True,
    )
    thread.start()
    return thread
