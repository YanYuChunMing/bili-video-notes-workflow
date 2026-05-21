import os
import json
import logging
import site

_nvidia_dll_dirs = []
try:
    for sp in site.getsitepackages():
        for sub in ("nvidia\\cublas\\bin", "nvidia\\cuda_runtime\\bin"):
            d = os.path.join(sp, sub)
            if os.path.isdir(d):
                os.add_dll_directory(d)
                _nvidia_dll_dirs.append(d)
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


def transcribe(
    audio_path: str,
    output_dir: str,
    model_name: str = "medium",
    language: str = "zh",
    device: str = "cuda",
    compute_type: str = "auto",
) -> dict:
    if _FASTER_WHISPER_AVAILABLE and device == "cuda":
        logger.info("使用 faster-whisper (CTranslate2 GPU 加速)")
        return _transcribe_faster_whisper(
            audio_path,
            output_dir,
            model_name=model_name,
            language=language,
            device=device,
            compute_type=compute_type,
        )
    else:
        logger.info(f"使用 openai-whisper (device={device})")
        return _transcribe_openai_whisper(
            audio_path,
            output_dir,
            model_name=model_name,
            language=language,
            device=device,
        )


def _transcribe_faster_whisper(
    audio_path: str,
    output_dir: str,
    model_name: str = "medium",
    language: str = "zh",
    device: str = "cuda",
    compute_type: str = "auto",
) -> dict:
    if compute_type == "auto":
        compute_type = "float16" if device == "cuda" else "int8"
    logger.info(
        f"加载 faster-whisper 模型: {model_name} "
        f"(device={device}, compute_type={compute_type})"
    )

    model = FasterWhisperModel(
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

    raw_text = result["text"].strip()
    segments = result.get("segments", [])

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
