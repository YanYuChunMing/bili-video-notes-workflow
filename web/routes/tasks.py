import os
import shutil

from fastapi import APIRouter, HTTPException

from web.models import ApiResponse, TaskCreateRequest, TaskInfo, TaskStatus
from web import task_manager

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("", response_model=ApiResponse)
def create_task(req: TaskCreateRequest):
    from src import config_loader

    if not req.urls:
        return ApiResponse(code=400, message="urls 不能为空").model_dump()

    config = config_loader.load_config("config.toml")

    created = []
    for url in req.urls:
        task = task_manager.create_task(url=url, mode=req.mode.value)
        created.append(task)
        task_manager.start_task(task.task_id, url, req.mode.value, config)

    return ApiResponse(data=[t.model_dump() for t in created]).model_dump()


@router.get("", response_model=ApiResponse)
def list_tasks(page: int = 1, page_size: int = 20):
    all_tasks = task_manager.get_all_tasks()
    total = len(all_tasks)

    start = (page - 1) * page_size
    end = start + page_size
    items = all_tasks[start:end]

    return ApiResponse(data={
        "items": [t.model_dump() for t in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }).model_dump()


@router.get("/{task_id}", response_model=ApiResponse)
def get_task(task_id: str):
    task = task_manager.get_task(task_id)
    if task is None:
        return ApiResponse(code=404, message="任务不存在").model_dump()
    return ApiResponse(data=task.model_dump()).model_dump()


@router.delete("/{task_id}", response_model=ApiResponse)
def delete_task(task_id: str):
    task = task_manager.get_task(task_id)
    if task is None:
        return ApiResponse(code=404, message="任务不存在").model_dump()

    active_statuses = {TaskStatus.pending, TaskStatus.downloading, TaskStatus.transcribing,
                       TaskStatus.cleaning, TaskStatus.summarizing, TaskStatus.mindmap,
                       TaskStatus.screenshot}
    if task.status in active_statuses:
        return ApiResponse(code=400, message="任务正在运行中，无法删除").model_dump()

    success = task_manager.delete_task(task_id)
    if success:
        return ApiResponse(message="已删除").model_dump()
    return ApiResponse(code=500, message="删除失败").model_dump()
