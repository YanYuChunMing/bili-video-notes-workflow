import os
import logging

import numpy as np

from .screenshotter import ScreenshotterInterface
from . import utils
from .learning_units import build_learning_units, generate_candidate_times

logger = logging.getLogger(__name__)


def compute_clarity_score(gray_frame: np.ndarray) -> float:
    laplacian = cv2.Laplacian(gray_frame, cv2.CV_64F)
    variance = laplacian.var()
    return min(1.0, variance / 800.0)


def compute_information_score(gray_frame: np.ndarray) -> float:
    gray_mean = np.mean(gray_frame)
    gray_std = np.std(gray_frame)

    if gray_mean < 10 or gray_mean > 245:
        return 0.0

    edges = cv2.Canny(gray_frame, 50, 150)
    edge_density = np.sum(edges > 0) / edges.size
    gray_std_norm = gray_std / 128.0

    score = min(1.0, edge_density * 3.0 + gray_std_norm * 0.5)

    if gray_std < 5:
        score *= 0.5

    return score


def compute_duplicate_penalty(gray_frame: np.ndarray, last_selected_gray: np.ndarray | None) -> float:
    if last_selected_gray is None:
        return 0.0

    small = cv2.resize(gray_frame, (160, 90))
    small_last = cv2.resize(last_selected_gray, (160, 90))
    ssim_result = structural_similarity(small, small_last)
    ssim_val = float(ssim_result[0]) if isinstance(ssim_result, tuple) else float(ssim_result)

    if ssim_val < 0.85:
        return 0.0
    return min(1.0, (ssim_val - 0.85) / 0.15)


def compute_stability_score(gray_frame: np.ndarray, prev_gray: np.ndarray | None, next_gray: np.ndarray | None) -> float:
    if prev_gray is None and next_gray is None:
        return 0.8

    similarities = []
    small = cv2.resize(gray_frame, (160, 90))

    if prev_gray is not None:
        small_prev = cv2.resize(prev_gray, (160, 90))
        ssim_result = structural_similarity(small, small_prev)
        ssim_val = float(ssim_result[0]) if isinstance(ssim_result, tuple) else float(ssim_result)
        similarities.append(ssim_val)
    if next_gray is not None:
        small_next = cv2.resize(next_gray, (160, 90))
        ssim_result = structural_similarity(small, small_next)
        ssim_val = float(ssim_result[0]) if isinstance(ssim_result, tuple) else float(ssim_result)
        similarities.append(ssim_val)

    if not similarities:
        return 0.8

    return sum(similarities) / len(similarities)


def compute_cue_bonus(sample_time: float, unit) -> float:
    bonus = 0.0

    if unit.unit_type == "operation":
        prefer_time = unit.start + 1.5
        dist = abs(sample_time - prefer_time)
        if dist < 2.0:
            bonus += (2.0 - dist) / 2.0 * 0.6

    if unit.unit_type == "result":
        dist = unit.end - sample_time
        if 0 <= dist <= 3.0:
            bonus += (3.0 - dist) / 3.0 * 0.8

    return min(1.0, bonus)


class LearningScreenshotter(ScreenshotterInterface):
    """
    学习单元驱动截图策略。

    输入：video_path, segments_path (Whisper segments JSON), output_dir
    流程：
    1. build_learning_units(segments) -> list[LearningUnit]
    2. generate_candidate_times(units, video_duration) -> 填充各 unit.candidate_times
    3. score_and_select_frames(video_path, units) -> 填充各 unit.selected_images
    4. save_screenshots(units, output_dir) -> 保存图片，返回 {timestamp: path}
    """

    def __init__(self, config: dict):
        super().__init__(config)
        self.max_per_unit = config["screenshot"].get("max_images_per_unit", 2)
        self.min_interval = config["screenshot"].get("min_interval_seconds", 3)
        self.prefer_after = config["screenshot"].get("prefer_after_action_seconds", 1.5)
        self.difference_threshold = config["screenshot"].get("difference_threshold", 0.85)

    def process(self, video_path: str, segments_path: str, output_dir: str) -> dict:
        if not self.enabled:
            return {}

        if not os.path.exists(video_path):
            logger.warning(f"视频文件不存在: {video_path}")
            return {}

        try:
            import cv2
            from skimage.metrics import structural_similarity as ssim_func
        except ImportError as e:
            logger.error(f"截图功能需要 opencv-python 和 scikit-image: {e}")
            return {}

        segments = utils.load_json(segments_path, [])
        if not segments:
            logger.warning("无 segments 数据，跳过截图")
            return {}

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"无法打开视频文件: {video_path}")
            return {}

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        video_duration = total_frames / fps if fps > 0 else 0
        cap.release()

        if fps <= 0 or video_duration <= 0:
            logger.error("无法获取视频信息")
            return {}

        units = build_learning_units(segments)
        units = generate_candidate_times(units, video_duration, segments)

        units = self._score_and_select_frames(video_path, units, fps, total_frames, video_duration, ssim_func, cv2)

        screenshots = self._save_learning_screenshots(video_path, units, output_dir, fps, total_frames, cv2)

        units_data = []
        for u in units:
            units_data.append({
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
        units_json_path = os.path.join(output_dir, "learning_units.json")
        utils.save_json(units_json_path, units_data)
        logger.info(f"学习单元数据已保存: {units_json_path}")

        logger.info(f"学习截图完成: {len(screenshots)} 张图片")
        return screenshots

    def _score_and_select_frames(self, video_path, units, fps, total_frames, video_duration, ssim_func, cv2):
        cap = cv2.VideoCapture(video_path)
        last_selected_gray = None
        last_selected_time = -self.min_interval

        for unit in units:
            if not unit.candidate_times:
                continue

            scored_candidates = []
            prev_sample_gray = None

            for t in unit.candidate_times:
                sample_grays = {}
                sample_frames = {}

                for offset in [-0.5, 0.0, 0.5, 1.0]:
                    sample_time = round(t + offset, 2)
                    sample_time = max(0.0, min(sample_time, video_duration))

                    frame_idx = int(sample_time * fps)
                    if frame_idx >= total_frames:
                        frame_idx = total_frames - 1
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                    ret, frame = cap.read()
                    if not ret:
                        continue

                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    sample_grays[offset] = gray
                    sample_frames[offset] = frame

                if 0.0 not in sample_grays:
                    continue

                for offset, gray in sample_grays.items():
                    sample_time = round(t + offset, 2)
                    sample_time = max(0.0, min(sample_time, video_duration))

                    clarity = compute_clarity_score(gray)
                    info_score = compute_information_score(gray)
                    dup_penalty = compute_duplicate_penalty(gray, last_selected_gray)

                    prev_gray = sample_grays.get(round(offset - 0.5, 1))
                    next_gray = sample_grays.get(round(offset + 0.5, 1))
                    stability = compute_stability_score(gray, prev_gray, next_gray)

                    cue_bonus = compute_cue_bonus(sample_time, unit)

                    score = (
                        clarity * 0.35
                        + stability * 0.25
                        + info_score * 0.20
                        + cue_bonus * 0.15
                        - dup_penalty * 0.30
                    )

                    scored_candidates.append({
                        "timestamp": sample_time,
                        "gray": gray,
                        "frame": sample_frames.get(offset),
                        "score": score,
                        "reason": f"clarity={clarity:.2f} stability={stability:.2f} info={info_score:.2f} cue={cue_bonus:.2f} dup={dup_penalty:.2f}",
                    })

            scored_candidates.sort(key=lambda x: x["score"], reverse=True)

            selected = []
            for cand in scored_candidates:
                if len(selected) >= self.max_per_unit:
                    break
                if cand["score"] < 0.1:
                    continue
                if abs(cand["timestamp"] - last_selected_time) < self.min_interval:
                    continue
                if cand.get("frame") is None:
                    continue
                selected.append(cand)
                last_selected_gray = cand["gray"]
                last_selected_time = cand["timestamp"]

            unit.selected_images = [
                {
                    "timestamp": s["timestamp"],
                    "path": "",
                    "reason": s["reason"],
                    "score": round(s["score"], 4),
                }
                for s in selected
            ]

        cap.release()
        return units

    def _save_learning_screenshots(self, video_path, units, output_dir, fps, total_frames, cv2) -> dict:
        images_dir = os.path.join(output_dir, "images")
        os.makedirs(images_dir, exist_ok=True)

        cap = cv2.VideoCapture(video_path)
        screenshots = {}

        for unit in units:
            for img in unit.selected_images:
                ts = img["timestamp"]
                frame_idx = int(ts * fps)
                if frame_idx >= total_frames:
                    frame_idx = total_frames - 1
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                if not ret:
                    continue

                filename = utils.timestamp_to_filename(ts) + ".jpg"
                filepath = os.path.join(images_dir, filename)

                if os.path.exists(filepath):
                    base, ext = os.path.splitext(filename)
                    filename = f"{base}_{int(ts * 100) % 100:02d}{ext}"
                    filepath = os.path.join(images_dir, filename)

                buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])[1]
                with open(filepath, "wb") as f:
                    f.write(buf.tobytes())

                relative_path = os.path.join("images", filename)
                img["path"] = relative_path
                screenshots[ts] = relative_path

        cap.release()
        return screenshots


try:
    import cv2
    from skimage.metrics import structural_similarity
except ImportError:
    pass
