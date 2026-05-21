# Changelog

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)（Semantic Versioning）规范。
所有值得注意的变更都会被记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 `MAJOR.MINOR.PATCH` 规则。

---

## [1.1.0] - 2026-05-22

### Added
- 新增 `_is_valid_api_key()` 校验函数，自动检测 API Key 是否为有效值，防止占位符引发崩溃

### Fixed
- **修复 GPU 转录 CUDA DLL 缺失崩溃**：CUDA 13 驱动环境中 `ctranslate2` 找不到 `cublas64_12.dll` 的问题。现在自动注册 NVIDIA CUDA 12 运行时 DLL 路径
- **修复 DeepSeek API Key 占位符导致 ASCII 编码崩溃**：当 `.env` 中填入中文占位符（如 `sk-你的API密钥填这里`）时，`httpx` 构建 Header 抛出 `UnicodeEncodeError`。现在 4 处 API 调用入口均增加 Key 有效性校验
- **修复 OpenCV `imwrite` 中文路径截图写入失败**：`cv2.imwrite` 对含全角冒号路径写入失败，截图日志显示完成但实际文件不存在。改用 `cv2.imencode` + Python `open(wb)` 写入 JPEG
- **修复断点续跑 Basic / With-Images 模式互斥跳过**：Basic 模式处理后，同 URL 的 With-Images 模式被错误跳过。现在支持 `URL + mode` 双重匹配
- **修复 With-Images 模式下 .md 图片显示空白**：`transcript_with_images.md` 中图片引用路径缺少 `../` 前缀，导致 Markdown 阅读器（幕布等）从 `results/` 出发解析路径时找不到实际位于上级目录的图片文件。修复为 `![截图](../segment_NNN/images/xxx.jpg)` 正确回退一层

### Changed
- `.gitignore` 新增 `metadata.json` 排除规则

---

## [1.0.0] - 2026-05-20

### Added

#### 核心工作流
- 完整的 B站视频 → 笔记端到端自动化处理流水线
- 双模式支持：`basic`（音频转录 + AI 笔记）和 `with_images`（完整视频 + 截图）

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
- `split_video()`：长视频（>60 分钟）自动 ffmpeg segment 切割
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

---

[1.1.0]: https://github.com/YanYuChunMing/bili-video-notes-workflow/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/YanYuChunMing/bili-video-notes-workflow/releases/tag/v1.0.0
