# Changelog

All notable changes to this project will be documented in this file.

---

## [1.0.0] - 2026-05-20

### Added

#### 核心工作流
- 完整的 B站视频 → 笔记端到端自动化处理流水线
- 双模式支持：`basic`（音频转录+AI笔记）和 `with_images`（完整视频+截图）

#### 链接解析 (`src/link_parser.py`)
- 支持三种 B站链接格式：`bilibili.com/video/`、`b23.tv` 短链、`bilibili.com/bangumi/play/`
- 自动去重与尾部标点清理
- 支持注释行（`#`）和空行跳过
- 可选 `bilibili_only` 模式：仅提取 B站链接或提取所有 URL

#### 媒体下载 (`src/downloader.py`)
- `download_audio()`：通过 yt-dlp 下载音频，输出 WAV（16kHz 单声道）
- `download_video()`：下载视频 MP4（≤1080p）+ 自动提取音频 + 自动分段
- ffmpeg GPU 硬件加速自动检测（CUDA / QSV）
- 下载超时保护：音频 30 分钟，视频 60 分钟
- yt-dlp `.info.json` 元数据解析

#### 视频分段 (`src/video_splitter.py`)
- `split_video()`：长视频（>60分钟）自动 ffmpeg segment 切割
- 流拷贝模式（`-c copy`），无转码损耗
- `filter_and_adjust_segments()`：Whisper 时间戳与分段视频时间轴适配
- `save_segments_report()`：生成切割报告 Markdown

#### 语音转录 (`src/transcriber.py`)
- 双后端自动选择：faster-whisper（CTranslate2 GPU 加速）优先，openai-whisper 回退
- faster-whisper VAD 静音过滤（`min_silence_duration_ms=500`）
- word-level 时间戳
- OpenCC 繁体→简体自动转换
- 三文件输出：纯文本、带时间戳 Markdown、结构化 JSON segments

#### AI 文本处理
- **标点补全** (`src/text_cleaner.py`)：DeepSeek API 驱动，分块策略处理长文本
- **摘要生成** (`src/summarizer.py`)：学习笔记风格 Markdown，长文本两次摘要策略
- **思维导图** (`src/mindmap.py`)：DeepSeek 生成结构化大纲 + Markdown→HTML 渲染

#### 智能截图 (`src/screenshotter.py`)
- 策略模式设计：`ScreenshotterInterface` 抽象基类 + `DefaultScreenshotter` 实现
- 候选时间点：长语义段取中间时刻，短语义段取起始时刻
- SSIM 结构相似度去重（默认阈值 0.85）
- 频率控制：最小间隔 5 秒，每分钟最多 5 张
- OpenCV 帧读取 + JPEG 85% 质量输出

#### Markdown 构建 (`src/markdown_builder.py`)
- `build_transcript_with_images()`：时间戳匹配，图文并茂笔记生成

#### 配置管理 (`src/config_loader.py`)
- 三层配置合并：内置默认值 → config.toml → .env 环境变量
- 深度合并（Deep Merge）策略
- 相对路径自动解析为项目根目录绝对路径
- 多任务定义支持（`[[tasks]]` 数组）

#### 工具函数 (`src/utils.py`)
- 双通道日志系统（文件 + 控制台）
- 文件名非法字符清理与长度限制
- 断点续跑：`processed.json` / `failed.json` 状态追踪
- 时间戳格式化（`seconds_to_timestamp` / `timestamp_to_filename`）

#### CLI (`main.py`)
- `--task`：按任务名运行
- `--input` + `--mode`：命令行直接指定
- `--config`：自定义配置文件路径
- 无参数运行：执行所有配置任务

#### 代码质量 (`_check.py`)
- pyright 全项目静态类型检查
- AST 编译语法检查

### Known Issues
- `basic` 模式不下载完整视频，仅下载音频
- `requirements.txt` 未声明 `yt-dlp` 依赖
- 未集成 B站 Cookie / 登录态支持
- 文字清洗模块不包含语句通顺度优化
