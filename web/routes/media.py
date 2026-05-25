import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from web import task_manager

router = APIRouter(prefix="/media", tags=["media"])


@router.get("/{task_id}/{filepath:path}")
def serve_media(task_id: str, filepath: str):
    task = task_manager.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")

    output_dir = task.output_dir
    if not output_dir:
        raise HTTPException(status_code=404, detail="产物目录不存在")

    full_path = os.path.normpath(os.path.join(output_dir, filepath))

    if not full_path.startswith(os.path.normpath(output_dir)):
        raise HTTPException(status_code=403, detail="禁止访问")

    if not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    return FileResponse(full_path)
