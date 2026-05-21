import os
import shutil
import sys
import argparse
import logging
import traceback

from src import config_loader
from src import utils
from src import link_parser
from src import downloader
from src import transcriber
from src import text_cleaner
from src import summarizer
from src import mindmap
from src import screenshotter
from src import markdown_builder
from src import video_splitter

logger = logging.getLogger("main")


def process_single_video(
    url: str,
    task_config: dict,
    config: dict,
    index: int,
) -> bool:
    mode = task_config.get("mode", "basic")
    with_images = mode == "with_images"
    screenshot_enabled = config["screenshot"].get("enabled", False) or with_images

    logger.info(f"[{index}] ===== 开始处理: {url} (mode={mode}) =====")

    try:
        download_dir = config_loader.resolve_path(config, "download_dir")
        output_base = config_loader.resolve_path(config, "output_dir")

        if with_images or screenshot_enabled:
            result = downloader.download_video(url, "", download_dir)
        else:
            result = downloader.download_audio(url, "", download_dir)

        title = result["title"]
        audio_path = result["audio_path"]
        video_path = result.get("video_path", "")
        video_segments = result.get("video_segments", [])

        output_dir = utils.generate_output_dirname(output_base, index, title)
        logger.info(f"[{index}] 输出目录: {output_dir}")

        if audio_path and not audio_path.startswith(output_dir):
            if not os.path.exists(os.path.join(output_dir, "audio.wav")):
                audio_relocate = os.path.join(output_dir, "audio.wav")
                if os.path.exists(audio_path):
                    shutil.copy2(audio_path, audio_relocate)
                    audio_path = audio_relocate

        transcribe_result = transcriber.transcribe(
            audio_path,
            output_dir,
            model_name=config["whisper"]["model"],
            language=config["whisper"]["language"],
            device=config["whisper"]["device"],
            compute_type=config["whisper"].get("compute_type", "auto"),
        )

        raw_text = transcribe_result["text"]
        segments = transcribe_result["segments"]

        punct_output_path = os.path.join(output_dir, "results", "transcript_with_punct.txt")
        cleaned_text = text_cleaner.clean_transcript_with_punctuation(
            config, raw_text, punct_output_path
        )

        summary_output_path = os.path.join(output_dir, "results", "summary.md")
        summarizer.generate_summary(config, cleaned_text, summary_output_path)

        mindmap.generate_mindmap(
            config,
            cleaned_text,
            os.path.join(output_dir, "results"),
        )

        if screenshot_enabled and video_segments:
            all_screenshots = {}
            for seg in video_segments:
                offset = seg["start_offset"]
                seg_video_path = seg["path"]
                seg_idx = seg["index"]

                adjusted = video_splitter.filter_and_adjust_segments(
                    segments, offset, seg["duration"]
                )
                if not adjusted:
                    continue

                seg_segments_path = os.path.join(
                    output_dir, f"segments_part_{seg_idx:03d}.json"
                )
                utils.save_json(seg_segments_path, adjusted)

                seg_output_dir = os.path.join(output_dir, f"segment_{seg_idx:03d}")
                os.makedirs(seg_output_dir, exist_ok=True)

                ss = screenshotter.DefaultScreenshotter(config)
                ss.enabled = True
                seg_screenshots = ss.process(
                    seg_video_path,
                    seg_segments_path,
                    seg_output_dir,
                )

                for ts, img_path in seg_screenshots.items():
                    global_ts = ts + offset
                    all_screenshots[global_ts] = (
                        f"segment_{seg_idx:03d}/{img_path}"
                    )

            if all_screenshots:
                markdown_builder.build_transcript_with_images(
                    segments, all_screenshots,
                    os.path.join(output_dir, "results"), title,
                )
                logger.info(f"[{index}] 带截图文字稿已生成")

            if len(video_segments) > 1:
                original_duration = sum(
                    s["duration"] for s in video_segments
                )
                video_splitter.save_segments_report(
                    video_segments,
                    original_duration,
                    os.path.join(output_dir, "results"),
                )

        processed_file = os.path.join(
            config_loader.get_project_root(), "processed.json"
        )
        utils.mark_url_processed(
            url, title, output_dir, mode, processed_file
        )

        logger.info(f"[{index}] ===== 处理完成: {title} =====")
        return True

    except Exception as e:
        logger.error(f"[{index}] 处理失败: {url}")
        logger.error(f"[{index}] 错误详情: {traceback.format_exc()}")

        failed_file = os.path.join(
            config_loader.get_project_root(), "failed.json"
        )
        utils.mark_url_failed(url, mode, str(e), failed_file)
        return False


def run_task(task_config: dict, config: dict):
    task_name = task_config.get("name", "unnamed")
    input_file = task_config.get("input_file", "links.txt")
    mode = task_config.get("mode", "basic")

    project_root = config_loader.get_project_root()
    log_dir = config_loader.resolve_path(config, "log_dir")
    utils.setup_logging(log_dir, task_name)

    logger.info(f"=== 启动任务: {task_name} ===")
    logger.info(f"模式: {mode}")
    logger.info(f"链接文件: {input_file}")

    input_path = input_file
    if not os.path.isabs(input_path):
        input_path = os.path.join(project_root, input_file)

    bilibili_only = task_config.get("bilibili_only", True)
    urls = link_parser.parse_links_file(input_path, bilibili_only=bilibili_only)

    if not urls:
        logger.warning(f"未从 {input_file} 中提取到有效链接，任务结束")
        return

    processed_file = os.path.join(project_root, "processed.json")
    failed_file = os.path.join(project_root, "failed.json")

    success_count = 0
    fail_count = 0
    skip_count = 0

    for i, url in enumerate(urls, 1):
        if utils.is_url_already_processed(url, processed_file):
            logger.info(f"[{i}/{len(urls)}] 已处理过，跳过: {url}")
            skip_count += 1
            continue

        success = process_single_video(url, task_config, config, i)
        if success:
            success_count += 1
        else:
            fail_count += 1


    logger.info(f"=== 任务完成: {task_name} ===")
    logger.info(
        f"总计 {len(urls)} 个链接 | "
        f"成功 {success_count} | 失败 {fail_count} | 跳过 {skip_count}"
    )

    processed = utils.load_json(processed_file, [])
    failed = utils.load_json(failed_file, [])
    logger.info(f"历史累计: 成功 {len(processed)}, 失败 {len(failed)}")


def main():
    parser = argparse.ArgumentParser(
        description="B站视频自动笔记生成工作流"
    )
    parser.add_argument(
        "--task",
        type=str,
        default=None,
        help="指定任务名称（对应 config.toml 中的 [[tasks]] name）",
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="指定链接文件路径",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["basic", "with_images"],
        default=None,
        help="运行模式: basic 或 with_images",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.toml",
        help="配置文件路径 (默认: config.toml)",
    )
    args = parser.parse_args()

    config = config_loader.load_config(args.config)

    if args.input and args.mode:
        task_config = {
            "name": "cli_task",
            "input_file": args.input,
            "mode": args.mode,
        }
        run_task(task_config, config)
        return

    if args.task:
        task_config = config_loader.get_task_by_name(config, args.task)
        if task_config is None:
            print(f"[ERROR] 未找到任务: {args.task}")
            print("可用任务:")
            for t in config_loader.get_tasks(config):
                print(f"  - {t.get('name', 'unnamed')}")
            sys.exit(1)
        run_task(task_config, config)
        return

    tasks = config_loader.get_tasks(config)
    if not tasks:
        print("[INFO] config.toml 中未定义任务。使用方法：")
        print("  python main.py --input links.txt --mode basic")
        print("  python main.py --task basic_test")
        return

    for task_config in tasks:
        run_task(task_config, config)


if __name__ == "__main__":
    main()
