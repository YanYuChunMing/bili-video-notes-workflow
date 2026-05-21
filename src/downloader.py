import os
import json
import logging
import subprocess

from . import utils
from . import video_splitter

logger = logging.getLogger(__name__)

_FFMPEG_GPU_SUPPORT = None


def _check_ffmpeg_gpu() -> str:
    global _FFMPEG_GPU_SUPPORT
    if _FFMPEG_GPU_SUPPORT is not None:
        return _FFMPEG_GPU_SUPPORT

    try:
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-hwaccels"],
            capture_output=True, text=True, timeout=10,
        )
        output = result.stdout
        if "cuda" in output:
            _FFMPEG_GPU_SUPPORT = "cuda"
        elif "qsv" in output:
            _FFMPEG_GPU_SUPPORT = "qsv"
        else:
            _FFMPEG_GPU_SUPPORT = ""
    except Exception:
        _FFMPEG_GPU_SUPPORT = ""

    if _FFMPEG_GPU_SUPPORT:
        logger.info(f"ffmpeg GPU 硬件加速可用: {_FFMPEG_GPU_SUPPORT}")
    else:
        logger.info("ffmpeg 未检测到 GPU 硬件加速支持，使用 CPU 解码")
    return _FFMPEG_GPU_SUPPORT


def download_audio(url: str, output_dir: str, download_dir: str) -> dict:
    os.makedirs(download_dir, exist_ok=True)

    logger.info(f"开始下载音频: {url}")

    audio_output_template = os.path.join(download_dir, "%(title)s.%(ext)s")
    metadata_output = os.path.join(output_dir, "metadata.json")

    cmd = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format", "wav",
        "--audio-quality", "0",
        "-o", audio_output_template,
        "--print", "after_move:filepath",
        "--write-info-json",
        "--no-playlist",
        url,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=download_dir,
            timeout=1800,
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip()
            logger.error(f"yt-dlp 下载失败: {error_msg}")
            raise RuntimeError(f"下载失败: {error_msg}")

        output_lines = [line for line in result.stdout.strip().split("\n") if line]
        audio_path = output_lines[-1] if output_lines else ""

        if not audio_path or not os.path.exists(audio_path):
            alt_files = [
                f for f in os.listdir(download_dir)
                if f.endswith(".wav")
            ]
            if alt_files:
                audio_path = os.path.join(download_dir, alt_files[-1])

        if not audio_path or not os.path.exists(audio_path):
            raise FileNotFoundError(f"未找到下载的音频文件: {audio_path}")

    except subprocess.TimeoutExpired:
        logger.error("下载超时（30分钟）")
        raise RuntimeError("下载超时")

    metadata = _extract_metadata(download_dir, audio_path)
    utils.save_json(metadata_output, metadata)

    title = metadata.get("title", "unknown")
    logger.info(f"音频下载完成: {title} -> {audio_path}")

    return {
        "audio_path": audio_path,
        "title": title,
        "metadata": metadata,
    }


def download_video(url: str, output_dir: str, download_dir: str) -> dict:
    os.makedirs(download_dir, exist_ok=True)

    logger.info(f"开始下载视频: {url}")

    video_output_template = os.path.join(download_dir, "%(title)s.%(ext)s")
    metadata_output = os.path.join(output_dir, "metadata.json")

    cmd = [
        "yt-dlp",
        "-f", "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
        "--merge-output-format", "mp4",
        "-o", video_output_template,
        "--print", "after_move:filepath",
        "--write-info-json",
        "--no-playlist",
        url,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=download_dir,
            timeout=3600,
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip()
            logger.error(f"yt-dlp 下载失败: {error_msg}")
            raise RuntimeError(f"下载失败: {error_msg}")

        output_lines = [line for line in result.stdout.strip().split("\n") if line]
        video_path = output_lines[-1] if output_lines else ""

        if not video_path or not os.path.exists(video_path):
            alt_files = [
                f for f in os.listdir(download_dir)
                if f.endswith((".mp4", ".mkv", ".webm"))
            ]
            if alt_files:
                video_path = os.path.join(download_dir, alt_files[-1])

        if not video_path or not os.path.exists(video_path):
            raise FileNotFoundError(f"未找到下载的视频文件: {video_path}")

    except subprocess.TimeoutExpired:
        logger.error("下载超时（60分钟）")
        raise RuntimeError("下载超时")

    metadata = _extract_metadata(download_dir, video_path)
    utils.save_json(metadata_output, metadata)

    title = metadata.get("title", "unknown")
    logger.info(f"视频下载完成: {title} -> {video_path}")

    audio_path = _extract_audio_from_video(video_path, output_dir)

    video_segments = video_splitter.split_video(video_path, output_dir)

    return {
        "video_path": video_path,
        "audio_path": audio_path,
        "title": title,
        "metadata": metadata,
        "video_segments": video_segments,
    }


def _extract_metadata(download_dir: str, media_path: str) -> dict:
    base_name = os.path.splitext(os.path.basename(media_path))[0]
    info_json_path = None

    for f in os.listdir(download_dir):
        if f.endswith(".info.json"):
            candidate_title = os.path.splitext(f)[0].replace(".info", "")
            candidate_base = base_name.rsplit(".", 1)[0] if "." in base_name else base_name
            if candidate_title in base_name or base_name in candidate_title:
                info_json_path = os.path.join(download_dir, f)
                break

    if not info_json_path:
        json_files = [f for f in os.listdir(download_dir) if f.endswith(".info.json")]
        if json_files:
            info_json_path = os.path.join(download_dir, json_files[-1])

    if info_json_path and os.path.exists(info_json_path):
        info = utils.load_json(info_json_path, {})
        return {
            "title": info.get("title", os.path.splitext(os.path.basename(media_path))[0]),
            "duration": info.get("duration", 0),
            "uploader": info.get("uploader", ""),
            "upload_date": info.get("upload_date", ""),
            "description": info.get("description", ""),
            "webpage_url": info.get("webpage_url", ""),
        }

    return {
        "title": os.path.splitext(os.path.basename(media_path))[0],
        "duration": 0,
        "uploader": "",
        "upload_date": "",
        "description": "",
        "webpage_url": "",
    }


def _extract_audio_from_video(video_path: str, output_dir: str) -> str:
    audio_path = os.path.join(output_dir, "audio.wav")

    gpu_backend = _check_ffmpeg_gpu()
    cmd = ["ffmpeg"]
    if gpu_backend:
        cmd += ["-hwaccel", gpu_backend]
    cmd += [
        "-i", video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        "-y",
        audio_path,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
        )
        if result.returncode != 0:
            logger.warning(f"从视频提取音频失败: {result.stderr}")
            return ""
    except Exception as e:
        logger.warning(f"提取音频异常: {e}")
        return ""

    logger.info(f"音频已提取: {audio_path}")
    return audio_path
