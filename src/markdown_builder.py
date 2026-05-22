import os
import logging

from . import utils
from .learning_units import LearningUnit

logger = logging.getLogger(__name__)


def build_transcript_with_images(
    segments: list,
    screenshots: dict,
    output_dir: str,
    title: str = "",
) -> str:
    output_path = os.path.join(output_dir, "transcript_with_images.md")

    lines = []
    if title:
        lines.append(f"# {title}\n")
    else:
        lines.append("# 带截图的视频文字稿\n")

    for seg in segments:
        start_ts = utils.seconds_to_timestamp(seg["start"])
        seg_text = seg["text"].strip()
        if not seg_text:
            continue

        lines.append(f"\n[{start_ts}] {seg_text}\n")

        seg_start = seg["start"]
        seg_end = seg.get("end", seg_start + 10)
        for ss_time, img_path in screenshots.items():
            if seg_start <= ss_time <= seg_end:
                ss_ts = utils.seconds_to_timestamp(ss_time)
                lines.append(f"![截图 {ss_ts}](../{img_path})\n")

    content = "\n".join(lines)
    utils.write_text_file(output_path, content)
    logger.info(f"带截图文字稿已保存: {output_path}")
    return content


def build_learning_transcript_with_images(
    learning_units: list,
    output_dir: str,
    title: str = "",
    video_duration: float = 0.0,
) -> str:
    output_path = os.path.join(output_dir, "learning_transcript_with_images.md")

    lines = []
    if title:
        lines.append(f"# {title}")
    else:
        lines.append("# 学习单元驱动图文稿")
    lines.append("")

    for i, unit in enumerate(learning_units, 1):
        lines.append("---")
        lines.append("")

        lines.append(f"## {i}. {unit.title}")
        lines.append("")

        start_ts = utils.seconds_to_timestamp(unit.start)
        end_ts = utils.seconds_to_timestamp(unit.end)
        lines.append(f"> 时间：{start_ts} - {end_ts}")
        lines.append(f"> 类型：{unit.unit_type} | 截图需求：{unit.visual_need}")
        lines.append("")

        for img in unit.selected_images:
            img_ts = utils.seconds_to_timestamp(img["timestamp"])
            img_path = img.get("path", "")
            if img_path:
                lines.append(f"![截图 {img_ts}](../{img_path})")
                lines.append(f"*截图原因：{img.get('reason', '')}（score={img.get('score', 0):.4f}）*")
                lines.append("")

        lines.append(unit.text)
        lines.append("")

    lines.append("---")
    lines.append("")

    total_units = len(learning_units)
    total_images = sum(len(u.selected_images) for u in learning_units)
    lines.append(f"> 共 {total_units} 个学习单元，{total_images} 张截图")

    content = "\n".join(lines)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    utils.write_text_file(output_path, content)
    logger.info(f"学习单元驱动图文稿已保存: {output_path}")
    return content


def save_learning_units_json(units: list, output_dir: str) -> str:
    data = []
    for u in units:
        data.append({
            "unit_id": u.unit_id,
            "title": u.title,
            "start": u.start,
            "end": u.end,
            "text": u.text,
            "unit_type": u.unit_type,
            "visual_need": u.visual_need,
            "cue_score": u.cue_score,
            "candidate_times": u.candidate_times,
            "selected_images": [
                {"timestamp": img["timestamp"], "path": img["path"], "reason": img["reason"], "score": img["score"]}
                for img in u.selected_images
            ],
        })
    filepath = os.path.join(output_dir, "learning_units.json")
    utils.save_json(filepath, data)
    logger.info(f"学习单元数据已保存: {filepath}")
    return filepath
