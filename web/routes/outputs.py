import os
import json

from fastapi import APIRouter, HTTPException

from web.models import ApiResponse
from web import task_manager

router = APIRouter(prefix="/api/outputs", tags=["outputs"])


def _get_output_dir(task_id: str) -> str:
    task = task_manager.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    output_dir = task.output_dir
    if not output_dir or not os.path.isdir(output_dir):
        raise HTTPException(status_code=404, detail="产物目录不存在")
    return output_dir


def _read_text_file(filepath: str) -> str:
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在")
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


@router.get("/{task_id}/summary")
def get_summary(task_id: str):
    output_dir = _get_output_dir(task_id)
    filepath = os.path.join(output_dir, "results", "summary.md")
    content = _read_text_file(filepath)
    return ApiResponse(data=content).model_dump()


@router.get("/{task_id}/mindmap")
def get_mindmap(task_id: str):
    output_dir = _get_output_dir(task_id)
    filepath = os.path.join(output_dir, "results", "mindmap.md")
    content = _read_text_file(filepath)
    return ApiResponse(data=content).model_dump()


@router.get("/{task_id}/mindmap.html")
def get_mindmap_html(task_id: str):
    output_dir = _get_output_dir(task_id)
    filepath = os.path.join(output_dir, "results", "mindmap.html")
    content = _read_text_file(filepath)
    return ApiResponse(data=content).model_dump()


@router.get("/{task_id}/transcript")
def get_transcript(task_id: str):
    output_dir = _get_output_dir(task_id)
    filepath = os.path.join(output_dir, "results", "transcript.txt")
    content = _read_text_file(filepath)
    return ApiResponse(data=content).model_dump()


@router.get("/{task_id}/transcript-punct")
def get_transcript_punct(task_id: str):
    output_dir = _get_output_dir(task_id)
    filepath = os.path.join(output_dir, "results", "transcript_with_punct.txt")
    content = _read_text_file(filepath)
    return ApiResponse(data=content).model_dump()


@router.get("/{task_id}/transcript-images")
def get_transcript_images(task_id: str):
    output_dir = _get_output_dir(task_id)
    filepath = os.path.join(output_dir, "results", "transcript_with_images.md")
    content = _read_text_file(filepath)
    return ApiResponse(data=content).model_dump()


@router.get("/{task_id}/metadata")
def get_metadata(task_id: str):
    output_dir = _get_output_dir(task_id)
    filepath = os.path.join(output_dir, "metadata.json")
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="metadata.json 不存在")
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return ApiResponse(data=data).model_dump()
