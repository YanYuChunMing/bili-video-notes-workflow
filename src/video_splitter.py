import os
import json
import logging
import subprocess

from . import utils

logger = logging.getLogger(__name__)


def get_video_duration(video_path: str) -> float:
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        video_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            logger.error(f"ffprobe 获取视频时长失败: {result.stderr.strip()}")
            return 0.0
        data = json.loads(result.stdout)
        return float(data.get("format", {}).get("duration", 0))
    except Exception as e:
        logger.error(f"获取视频时长异常: {e}")
        return 0.0


def split_video(
    video_path: str,
    output_dir: str,
    max_duration_minutes: int = 60,
) -> list[dict]:
    max_duration_seconds = max_duration_minutes * 60

    duration = get_video_duration(video_path)
    if duration <= 0:
        logger.error(f"无法获取视频时长，不进行切割: {video_path}")
        return [{
            "path": video_path,
            "start_offset": 0.0,
            "duration": 0.0,
            "index": 1,
        }]

    if duration <= max_duration_seconds:
        logger.info(
            f"视频时长 {duration/60:.1f} 分钟，"
            f"未超过 {max_duration_minutes} 分钟上限，无需切割"
        )
        return [{
            "path": video_path,
            "start_offset": 0.0,
            "duration": duration,
            "index": 1,
        }]

    logger.info(
        f"视频时长 {duration/60:.1f} 分钟，开始切割 "
        f"(每段 ≤{max_duration_minutes} 分钟)..."
    )

    os.makedirs(output_dir, exist_ok=True)

    output_template = os.path.join(output_dir, "video_part_%03d.mp4")

    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-c", "copy",
        "-map", "0",
        "-segment_time", str(max_duration_seconds),
        "-f", "segment",
        "-reset_timestamps", "1",
        "-y",
        output_template,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=7200,
        )
        if result.returncode != 0:
            logger.error(f"ffmpeg 切割失败: {result.stderr.strip()}")
            return [{
                "path": video_path,
                "start_offset": 0.0,
                "duration": duration,
                "index": 1,
            }]
    except subprocess.TimeoutExpired:
        logger.error("视频切割超时（2小时）")
        return [{
            "path": video_path,
            "start_offset": 0.0,
            "duration": duration,
            "index": 1,
        }]

    segments = []
    cumulative = 0.0
    idx = 0

    while True:
        seg_path = os.path.join(output_dir, f"video_part_{idx:03d}.mp4")
        if not os.path.exists(seg_path):
            break
        seg_duration = get_video_duration(seg_path)
        segments.append({
            "path": seg_path,
            "start_offset": cumulative,
            "duration": seg_duration,
            "index": idx + 1,
        })
        cumulative += seg_duration
        idx += 1

    if not segments:
        logger.error("切割后未找到任何分段文件，回退使用原始视频")
        return [{
            "path": video_path,
            "start_offset": 0.0,
            "duration": duration,
            "index": 1,
        }]

    total_seg = sum(s["duration"] for s in segments)
    logger.info(f"切割完成: {len(segments)} 个片段")
    for seg in segments:
        logger.info(
            f"  片段 {seg['index']}: "
            f"{seg['duration']/60:.1f} 分钟 | "
            f"{os.path.basename(seg['path'])}"
        )
    logger.info(
        f"  原始总时长: {duration/60:.1f} 分钟, "
        f"分段合计: {total_seg/60:.1f} 分钟"
    )

    return segments


def save_segments_report(
    segments: list[dict],
    original_duration: float,
    output_dir: str,
) -> str:
    report_path = os.path.join(output_dir, "video_segments_report.md")

    total_dur = sum(s["duration"] for s in segments)

    lines = [
        "# 视频切割报告",
        "",
        f"- 原始视频总时长: {original_duration/60:.1f} 分钟 "
        f"({original_duration:.1f} 秒)",
        f"- 切割片段数量: {len(segments)}",
        f"- 每段最大时长限制: 60 分钟",
        "",
        "| 序号 | 文件名 | 时长(分钟) | 时长(秒) | 起始偏移(秒) |",
        "|------|--------|------------|----------|-------------|",
    ]

    for seg in segments:
        lines.append(
            f"| {seg['index']} | {os.path.basename(seg['path'])} | "
            f"{seg['duration']/60:.1f} | {seg['duration']:.1f} | "
            f"{seg['start_offset']:.1f} |"
        )

    lines.append(
        f"| **合计** | | **{total_dur/60:.1f}** | **{total_dur:.1f}** | |"
    )

    content = "\n".join(lines)
    utils.write_text_file(report_path, content)
    logger.info(f"切割报告已保存: {report_path}")
    return report_path


def filter_and_adjust_segments(
    original_segments: list,
    offset: float,
    seg_duration: float,
) -> list[dict]:
    seg_end = offset + seg_duration
    adjusted = []
    for s in original_segments:
        s_start = s.get("start", 0)
        s_end = s.get("end", s_start)
        if s_end > offset and s_start < seg_end:
            new_seg = dict(s)
            new_seg["start"] = max(s_start - offset, 0)
            new_seg["end"] = min(s_end - offset, seg_duration)
            adjusted.append(new_seg)
    return adjusted
