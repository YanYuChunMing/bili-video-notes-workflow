import os
import logging

from . import utils

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
                lines.append(f"![截图 {ss_ts}]({img_path})\n")

    content = "\n".join(lines)
    utils.write_text_file(output_path, content)
    logger.info(f"带截图文字稿已保存: {output_path}")
    return content
