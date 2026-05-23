import os
import json
import logging
import site
import sys

_nvidia_dll_dirs = []
try:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidate_roots = []

    for sp in site.getsitepackages():
        candidate_roots.append(sp)

    candidate_roots.extend([
        os.path.join(sys.prefix, "Lib", "site-packages"),
        os.path.join(project_root, "venv", "Lib", "site-packages"),
        os.path.join(project_root, ".venv", "Lib", "site-packages"),
    ])

    seen_roots = set()
    for sp in candidate_roots:
        sp = os.path.abspath(sp)
        if sp in seen_roots:
            continue
        seen_roots.add(sp)
        for sub in (
            "nvidia\\cublas\\bin",
            "nvidia\\cuda_runtime\\bin",
            "nvidia\\cudnn\\bin",
            "ctranslate2",
        ):
            d = os.path.join(sp, sub)
            if os.path.isdir(d):
                handle = os.add_dll_directory(d)
                _nvidia_dll_dirs.append((d, handle))
                current_path = os.environ.get("PATH", "")
                path_parts = current_path.split(os.pathsep) if current_path else []
                if d not in path_parts:
                    os.environ["PATH"] = d + os.pathsep + current_path
except Exception:
    pass

from . import utils

logger = logging.getLogger(__name__)

try:
    from opencc import OpenCC
    _CC = OpenCC("t2s")
except ImportError:
    _CC = None
    logger.warning("OpenCC 未安装，将跳过繁体转简体")

_FASTER_WHISPER_AVAILABLE = False
try:
    from faster_whisper import WhisperModel as FasterWhisperModel
    _FASTER_WHISPER_AVAILABLE = True
except ImportError:
    logger.warning("faster-whisper 未安装，回退使用 openai-whisper")


def _resolve_openai_whisper_model_name(model_name: str) -> str:
    known = {
        "tiny", "tiny.en", "base", "base.en",
        "small", "small.en", "medium", "medium.en",
        "large-v1", "large-v2", "large-v3", "large", "turbo",
    }
    if model_name in known:
        return model_name

    if os.path.isdir(model_name):
        dir_name = os.path.basename(os.path.normpath(model_name))
        for prefix in ("faster-whisper-", "whisper-"):
            if dir_name.startswith(prefix):
                size = dir_name[len(prefix):]
                if size in known:
                    logger.info(
                        f"[模型名映射] {model_name} -> openai-whisper '{size}'"
                    )
                    return size
                break

    logger.warning(
        f"[模型名映射] 无法将 '{model_name}' 映射到 openai-whisper 内置模型，"
        f"将使用默认值 'medium'"
    )
    return "medium"


def transcribe(
    audio_path: str,
    output_dir: str,
    model_name: str = "medium",
    language: str = "zh",
    device: str = "cuda",
    compute_type: str = "auto",
) -> dict:
    if _FASTER_WHISPER_AVAILABLE:
        try:
            logger.info("=== GPU 加速阶段：尝试 faster-whisper (CTranslate2) ===")
            return _transcribe_faster_whisper(
                audio_path,
                output_dir,
                model_name=model_name,
                language=language,
                device=device,
                compute_type=compute_type,
            )
        except Exception as e:
            logger.warning(
                f"[CPU 回退] faster-whisper 在 device='{device}' 下失败: {e}"
            )
            logger.warning(
                "[CPU 回退] 原因：CUDA/cuBLAS 库不可用、GPU 驱动不兼容或显存不足"
            )

            try:
                logger.info(
                    "[CPU 回退] 第1级回退：尝试 faster-whisper (CPU 模式)"
                )
                return _transcribe_faster_whisper(
                    audio_path,
                    output_dir,
                    model_name=model_name,
                    language=language,
                    device="cpu",
                    compute_type="int8",
                )
            except Exception as e2:
                logger.warning(
                    f"[CPU 回退] faster-whisper CPU 模式也失败: {e2}"
                )

    logger.warning(
        "[CPU 回退] 第2级回退：切换到 openai-whisper (CPU 模式)"
    )
    logger.warning(
        "[CPU 回退] 注意：CPU 模式下语音转录速度较慢，"
        "约为 GPU 模式的 5-10 倍，请耐心等待"
    )

    resolved_model = _resolve_openai_whisper_model_name(model_name)
    if resolved_model != model_name:
        logger.info(
            f"[CPU 回退] 模型名已映射: '{model_name}' -> '{resolved_model}'"
        )

    return _transcribe_openai_whisper(
        audio_path,
        output_dir,
        model_name=resolved_model,
        language=language,
        device="cpu",
    )


def _transcribe_faster_whisper(
    audio_path: str,
    output_dir: str,
    model_name: str = "medium",
    language: str = "zh",
    device: str = "cuda",
    compute_type: str = "auto",
) -> dict:
    if not _FASTER_WHISPER_AVAILABLE:
        raise RuntimeError("faster-whisper 不可用")

    from faster_whisper import WhisperModel as FWModel  # type: ignore[no-redef]

    if compute_type == "auto":
        compute_type = "float16" if device == "cuda" else "int8"
    logger.info(
        f"加载 faster-whisper 模型: {model_name} "
        f"(device={device}, compute_type={compute_type})"
    )

    model = FWModel(
        model_name,
        device=device,
        compute_type=compute_type,
        cpu_threads=4,
        num_workers=2,
    )

    logger.info(f"开始转录: {audio_path}")
    seg_generator, info = model.transcribe(
        audio_path,
        language=language if language != "Chinese" else "zh",
        word_timestamps=True,
        vad_filter=True,
        vad_parameters=dict(
            min_silence_duration_ms=500,
        ),
    )

    segments = []
    for seg in seg_generator:
        segments.append({
            "start": seg.start,
            "end": seg.end,
            "text": seg.text.strip(),
        })

    raw_text = " ".join(s["text"] for s in segments if s["text"])

    logger.info(f"转录完成，共 {len(segments)} 个片段")

    raw_text = _convert_t2s(raw_text)
    for seg_item in segments:
        seg_item["text"] = _convert_t2s(seg_item.get("text", ""))

    return _save_transcribe_output(
        raw_text, segments, output_dir
    )


def _transcribe_openai_whisper(
    audio_path: str,
    output_dir: str,
    model_name: str = "medium",
    language: str = "zh",
    device: str = "cuda",
) -> dict:
    import whisper

    logger.info(f"加载 Whisper 模型: {model_name} (device={device})")
    model = whisper.load_model(model_name, device=device)
    logger.info(f"Whisper 模型加载完成，开始转录: {audio_path}")

    result = model.transcribe(
        audio_path,
        language=language,
        verbose=False,
        word_timestamps=True,
    )

    logger.info(f"转录完成，共 {len(result.get('segments', []))} 个片段")

    raw_text: str = str(result.get("text", "")).strip()
    segments: list[dict] = result.get("segments", [])  # type: ignore[assignment]

    raw_text = _convert_t2s(raw_text)
    for seg in segments:
        seg["text"] = _convert_t2s(seg.get("text", ""))

    return _save_transcribe_output(
        raw_text, segments, output_dir
    )


def _save_transcribe_output(
    raw_text: str,
    segments: list,
    output_dir: str,
) -> dict:
    results_dir = os.path.join(output_dir, "results")
    os.makedirs(results_dir, exist_ok=True)

    transcript_path = os.path.join(results_dir, "transcript.txt")
    utils.write_text_file(transcript_path, raw_text)

    timestamp_md = _build_timestamp_markdown(segments, raw_text)
    timestamp_path = os.path.join(results_dir, "transcript_with_timestamps.md")
    utils.write_text_file(timestamp_path, timestamp_md)

    segments_path = os.path.join(output_dir, "segments.json")
    utils.save_json(segments_path, segments)

    logger.info(f"转录文件已保存到: {results_dir}")

    return {
        "text": raw_text,
        "segments": segments,
        "transcript_path": transcript_path,
        "timestamp_md_path": timestamp_path,
        "segments_path": segments_path,
    }


def _convert_t2s(text: str) -> str:
    if _CC is None:
        return text
    try:
        return _CC.convert(text)
    except Exception:
        return text


def _build_timestamp_markdown(segments: list, full_text: str) -> str:
    lines = ["# 带时间戳的文字稿\n"]
    for seg in segments:
        start_ts = utils.seconds_to_timestamp(seg["start"])
        seg_text = seg.get("text", "").strip()
        if seg_text:
            lines.append(f"[{start_ts}] {seg_text}\n")

    lines.append("\n---\n")
    lines.append("# 纯文字稿\n")
    lines.append(full_text)

    return "\n".join(lines)
