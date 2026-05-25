import json
import logging
import asyncio
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from web import task_manager

logger = logging.getLogger("web.ws")
router = APIRouter()

_active_connections: dict[str, list[WebSocket]] = {}


@router.websocket("/ws/tasks/{task_id}")
async def websocket_task_progress(websocket: WebSocket, task_id: str):
    await websocket.accept()

    if task_id not in _active_connections:
        _active_connections[task_id] = []
    _active_connections[task_id].append(websocket)

    task = task_manager.get_task(task_id)
    if task:
        await websocket.send_json({
            "type": "progress",
            "task_id": task_id,
            "stage": task.status.value,
            "message": task.stage_message,
            "progress": task.progress,
            "timestamp": datetime.now().isoformat(),
        })

    try:
        last_progress = task.progress if task else 0.0
        while True:
            await asyncio.sleep(2)

            current_task = task_manager.get_task(task_id)
            if current_task is None:
                await websocket.send_json({
                    "type": "error",
                    "task_id": task_id,
                    "message": "任务已删除",
                    "timestamp": datetime.now().isoformat(),
                })
                break

            if (current_task.status.value != last_progress or
                    current_task.progress != last_progress):
                last_progress = current_task.progress
                await websocket.send_json({
                    "type": "progress",
                    "task_id": task_id,
                    "stage": current_task.status.value,
                    "message": current_task.stage_message,
                    "progress": current_task.progress,
                    "timestamp": datetime.now().isoformat(),
                })

            if current_task.status in (task_manager.TaskStatus.completed,
                                         task_manager.TaskStatus.failed):
                await websocket.send_json({
                    "type": "complete",
                    "task_id": task_id,
                    "status": current_task.status.value,
                    "message": current_task.stage_message,
                    "progress": current_task.progress,
                    "timestamp": datetime.now().isoformat(),
                })
                break

    except WebSocketDisconnect:
        logger.info(f"WebSocket 断开: task_id={task_id}")
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}")
    finally:
        if task_id in _active_connections:
            _active_connections[task_id].remove(websocket)
            if not _active_connections[task_id]:
                del _active_connections[task_id]
