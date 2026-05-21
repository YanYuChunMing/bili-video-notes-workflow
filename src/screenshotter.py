import os
import logging

logger = logging.getLogger(__name__)


class ScreenshotterInterface:
    """
    截图模块预留接口。

    后续实现时，子类需要实现 process() 方法：
    - 读取 video.mp4 和 segments.json
    - 根据 segment 时间点抽帧
    - 用 SSIM 判断画面差异
    - 控制截图数量（avg <= max_avg_per_minute）
    - 输出 images/ 目录
    - 返回 {timestamp: image_path} 映射

    当前为占位实现，不执行实际截图操作。
    """

    def __init__(self, config: dict):
        self.config = config
        self.min_interval = config["screenshot"].get("min_interval_seconds", 5)
        self.max_per_minute = config["screenshot"].get("max_avg_per_minute", 5)
        self.threshold = config["screenshot"].get("difference_threshold", 0.85)
        self.enabled = config["screenshot"].get("enabled", False)

    def process(
        self,
        video_path: str,
        segments_path: str,
        output_dir: str,
    ) -> dict:
        """
        执行截图处理。

        Args:
            video_path: 视频文件路径
            segments_path: Whisper segments JSON 文件路径
            output_dir: 输出目录（images 子目录将创建在此之下）

        Returns:
            dict: {timestamp_seconds: image_relative_path} 映射
        """
        if not self.enabled:
            logger.info("截图功能未启用")
            return {}

        if not os.path.exists(video_path):
            logger.warning(f"视频文件不存在，跳过截图: {video_path}")
            return {}

        logger.warning(
            "截图模块尚未完全实现。当前返回空结果。"
            "请实现 ScreenshotterInterface 的子类并重写 process() 方法。"
        )

        return {}


class DefaultScreenshotter(ScreenshotterInterface):
    """
    默认截图实现。

    使用 OpenCV + scikit-image SSIM 进行智能截图。
    需要安装: pip install opencv-python scikit-image

    功能：
    1. 根据 segments.json 中的时间段确定截图时间点
    2. 每个较长的语义段至少对应一张截图
    3. 用 SSIM 判断画面变化，过滤相似截图
    4. 控制每分钟最大截图数量
    5. 最小截图间隔 >= min_interval_seconds
    """

    def process(
        self,
        video_path: str,
        segments_path: str,
        output_dir: str,
    ) -> dict:
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

        from . import utils

        segments = utils.load_json(segments_path, [])
        if not segments:
            logger.warning("无 segments 数据，跳过截图")
            return {}

        images_dir = os.path.join(output_dir, "images")
        os.makedirs(images_dir, exist_ok=True)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"无法打开视频文件: {video_path}")
            return {}

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0

        if fps <= 0 or duration <= 0:
            logger.error("无法获取视频信息")
            cap.release()
            return {}

        candidate_times = _get_candidate_times(
            segments, self.min_interval, self.max_per_minute, duration
        )

        screenshots = {}
        last_screenshot_time = -self.min_interval
        last_gray = None

        for target_time in candidate_times:
            actual_count = len(screenshots)
            if actual_count > 0:
                actual_rate = actual_count / (target_time / 60.0)
                if actual_rate > self.max_per_minute:
                    continue

            if target_time - last_screenshot_time < self.min_interval:
                continue

            frame_idx = int(target_time * fps)
            if frame_idx >= total_frames:
                frame_idx = total_frames - 1
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if not ret:
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray_resized = cv2.resize(gray, (160, 90))

            if last_gray is not None:
                try:
                    ssim_val = ssim_func(last_gray, gray_resized)
                    if ssim_val > self.threshold:
                        continue
                except Exception:
                    pass

            filename = utils.timestamp_to_filename(target_time) + ".jpg"
            filepath = os.path.join(images_dir, filename)
            buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])[1]
            with open(filepath, "wb") as f:
                f.write(buf.tobytes())

            screenshots[target_time] = os.path.join("images", filename)
            last_screenshot_time = target_time
            last_gray = gray_resized

        cap.release()

        logger.info(f"截图完成: {len(screenshots)} 张图片 -> {images_dir}")
        return screenshots


def _get_candidate_times(
    segments: list,
    min_interval: float,
    max_per_minute: float,
    duration: float,
) -> list[float]:
    times = []
    min_segment_duration = 15.0

    for seg in segments:
        seg_start = seg.get("start", 0)
        seg_end = seg.get("end", 0)
        seg_duration = seg_end - seg_start

        if seg_duration >= min_segment_duration:
            times.append(seg_start + seg_duration / 2)
        else:
            times.append(seg_start)

    if not times and duration > 0:
        ideal_interval = 60.0 / max_per_minute
        t = ideal_interval
        while t < duration:
            times.append(t)
            t += ideal_interval

    times.sort()
    return times
