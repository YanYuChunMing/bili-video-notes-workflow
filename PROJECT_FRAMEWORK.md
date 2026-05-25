# B站视频自动笔记生成工作流 — 项目框架文档

---

## 目录

1. [项目架构概述](#1-项目架构概述)
   - 1.1 项目简介
   - 1.2 整体技术栈
   - 1.3 模块划分与目录结构
   - 1.4 核心组件及其交互关系
2. [接口信息汇总](#2-接口信息汇总)
   - 2.1 命令行接口 (CLI)
   - 2.2 外部 API 接口
   - 2.3 核心模块内部函数接口
   - 2.4 配置文件接口
3. [功能说明](#3-功能说明)
   - 3.1 链接解析模块
   - 3.2 媒体下载模块
   - 3.3 视频分段模块
   - 3.4 语音转录模块
   - 3.5 文字清洗模块
   - 3.6 摘要生成模块
   - 3.7 思维导图生成模块
   - 3.8 智能截图模块
   - 3.9 Markdown 构建模块
   - 3.10 配置管理模块
   - 3.11 工具函数模块
4. [使用手册](#4-使用手册)
   - 4.1 环境配置要求
   - 4.2 部署步骤
   - 4.3 启动方法
   - 4.4 日常操作流程
   - 4.5 常见问题排查
5. [数据结构说明](#5-数据结构说明)
   - 5.1 核心数据模型
   - 5.2 文件存储结构
   - 5.3 持久化数据格式
6. [关键业务流程](#6-关键业务流程)
   - 6.1 整体处理流程
   - 6.2 Basic 模式流程
   - 6.3 With-Images 模式流程
   - 6.4 断点续跑机制
7. [Web 平台](#7-web-平台)
   - 7.1 概述
   - 7.2 技术栈
   - 7.3 快速启动
   - 7.4 相关文档
8. [已知问题与限制](#8-已知问题与限制)
   - 8.1 部署就绪性问题
   - 8.2 视频下载相关限制
   - 8.3 功能边界说明
9. [版本历史](#9-版本历史)
10. [贡献指南](#10-贡献指南)

---

## 1. 项目架构概述

### 1.1 项目简介

**项目名称**：`bili-video-notes-workflow`

**项目目标**：自动化处理 B站（bilibili.com）视频，将其转化为结构化的学习笔记。核心能力包括：

- 自动下载 B站 视频/音频
- 使用 Whisper 进行高精度语音转录（支持 GPU 加速）
- 通过大语言模型（DeepSeek）进行标点补全、摘要生成、思维导图生成
- 可选智能截图并生成图文并茂的笔记

**适用场景**：网课学习、知识视频归档、会议记录整理、内容二次创作。

### 1.2 整体技术栈

| 层次 | 技术/工具 | 说明 |
|------|-----------|------|
| **语言** | Python 3.x | 核心开发语言 |
| **媒体下载** | yt-dlp | B站视频/音频下载 |
| **媒体处理** | ffmpeg / ffprobe | 音频提取、视频切割、时长检测 |
| **语音转录** | faster-whisper / openai-whisper | 语音转文字，支持 GPU(CUDA)/CPU |
| **AI 文本处理** | DeepSeek API (OpenAI 兼容) | 标点补全、段落整理、摘要、思维导图 |
| **繁简转换** | OpenCC | 繁体中文 → 简体中文 |
| **智能截图** | OpenCV + scikit-image (SSIM) | 视频关键帧提取与去重 |
| **配置管理** | TOML + python-dotenv | 配置文件 (.toml) + 环境变量 (.env) |
| **日志系统** | Python logging | 文件 + 控制台双通道日志 |

### 1.3 模块划分与目录结构

```
bili_video/                        # 项目根目录
├── main.py                        # 主入口，流程编排
├── _check.py                      # 代码质量检查脚本 (pyright + AST)
├── requirements.txt               # Python 依赖清单
├── config.toml                    # 用户配置文件 (需自行创建)
├── config.example.toml            # 配置文件模板
├── .env                           # 环境变量 (API Key 等敏感信息)
├── .env.example                   # 环境变量模板
├── links.txt                      # Basic 模式链接输入文件
├── links_with_images.txt          # With-Images 模式链接输入文件
│
└── src/                           # 核心源码模块
    ├── __init__.py                # 包初始化
    ├── config_loader.py           # 配置加载器
    ├── link_parser.py             # 链接解析器
    ├── downloader.py              # 媒体下载器
    ├── video_splitter.py          # 视频分段器
    ├── transcriber.py             # 语音转录器
    ├── text_cleaner.py            # 文字清洗器 (AI 标点补全)
    ├── summarizer.py              # 摘要生成器 (AI 学习笔记)
    ├── mindmap.py                 # 思维导图生成器 (AI)
    ├── screenshotter.py           # 智能截图器
    ├── markdown_builder.py        # Markdown 文档构建器
    └── utils.py                   # 通用工具函数
```

### 1.4 核心组件及其交互关系

```
                         ┌──────────────────────┐
                         │      main.py          │
                         │   (流程编排 & CLI)    │
                         └──────┬───────────────┘
                                │
        ┌───────────────────────┼───────────────────────────┐
        │                       │                            │
        ▼                       ▼                            ▼
┌───────────────┐    ┌──────────────────┐    ┌──────────────────────┐
│ config_loader │    │   link_parser    │    │       utils          │
│ (配置加载)    │    │  (链接解析)      │    │  (日志/文件/JSON)     │
└───────────────┘    └──────────────────┘    └──────────────────────┘
        │                       │
        ▼                       ▼
┌───────────────┐    ┌──────────────────┐
│  downloader   │    │  video_splitter  │
│ (视频/音频)   │◄───│  (视频分段)      │
│  yt-dlp       │    │  ffmpeg          │
└───────┬───────┘    └──────────────────┘
        │
        ▼
┌───────────────┐
│  transcriber  │
│  (Whisper)    │
└───────┬───────┘
        │
        ▼
┌───────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ text_cleaner  │     │   summarizer    │     │   mindmap       │
│ (DeepSeek API)│     │  (DeepSeek API) │     │ (DeepSeek API)  │
└───────────────┘     └─────────────────┘     └─────────────────┘
        │
        ▼
┌───────────────┐     ┌──────────────────┐
│screenshotter  │     │ markdown_builder │
│(OpenCV+SSIM)  │────►│ (图文笔记整合)   │
└───────────────┘     └──────────────────┘
```

**数据流向**：

```
链接文件(links.txt)
    │
    ▼
yt-dlp 下载 ──► 音频(.wav) ──► Whisper 转录 ──► 时间戳文字稿
                     │
                     ▼ (with_images 模式)
                ffmpeg 视频切割 ──► 视频分段 ──► OpenCV 截图
                                                        │
                                                        ▼
                                              Markdown 图文笔记
                                
                    转录文字
                        │
                        ▼
              DeepSeek 标点补全 ──► 分段整理后的文本
                        │
              ┌─────────┼─────────┐
              ▼                   ▼
        DeepSeek 摘要         DeepSeek 思维导图
        (summary.md)         (mindmap.md + .html)
```

---

## 2. 接口信息汇总

### 2.1 命令行接口 (CLI)

#### 2.1.1 程序入口

**命令**：`python main.py [选项]`

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `--task` | `str` | 否 | `None` | 指定任务名称（对应 config.toml 中 `[[tasks]]` 的 `name`） |
| `--input` | `str` | 否 | `None` | 指定链接文件路径 |
| `--mode` | `str` | 否 | `None` | 运行模式：`basic` 或 `with_images` |
| `--config` | `str` | 否 | `config.toml` | 配置文件路径 |

**使用示例**：

```bash
# 方式1：使用配置文件中的任务定义
python main.py --task basic_test

# 方式2：直接通过命令行参数指定
python main.py --input links.txt --mode basic

# 方式3：指定自定义配置文件
python main.py --config my_config.toml --task my_task

# 方式4：不传参数，运行 config.toml 中所有任务
python main.py
```

**执行逻辑**（参见 [main.py:L213-L274](file:///d:/AAA_MY/AAAMyGit/bili_video/main.py#L213-L274)）：

1. 解析命令行参数
2. 加载配置文件（默认 `config.toml`）
3. 优先级：`--input + --mode` > `--task` > 所有 `[[tasks]]`
4. 执行对应任务

#### 2.1.2 代码质量检查

**命令**：`python _check.py`

功能：对全项目 Python 文件执行 `pyright` 静态类型检查 和 `AST` 编译检查。

### 2.2 外部 API 接口

本项目需要调用以下外部服务 API：

#### 2.2.1 DeepSeek API（文本处理）

| 项目 | 说明 |
|------|------|
| **基础 URL** | `https://api.deepseek.com`（可配置） |
| **认证方式** | API Key（通过 `.env` 文件配置） |
| **模型** | `deepseek-chat`（可配置） |
| **调用方式** | OpenAI Python SDK (`openai.OpenAI`) |

**API 端点**：`POST {base_url}/v1/chat/completions`

**请求参数**（每次调用通用结构）：

| 参数 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `model` | `str` | 必填 | 模型名称，默认 `deepseek-chat` |
| `messages` | `list[dict]` | 必填 | 消息列表，每项含 `role` 和 `content` |
| `temperature` | `float` | 0-2 | 生成温度，默认 `0.3` |
| `max_tokens` | `int` | ≤8192 | 最大输出 token 数，默认 `4096` |

**重试机制**：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `max_retries` | `3` | 最大重试次数 |
| `retry_delay_seconds` | `5` | 重试间隔（秒），指数递增 |

**功能调用**：本项目通过 DeepSeek API 实现以下功能：

| 功能 | 调用模块 | System Prompt 角色 |
|------|----------|-------------------|
| 标点补全与段落整理 | [text_cleaner.py](file:///d:/AAA_MY/AAAMyGit/bili_video/src/text_cleaner.py) | 中文文字整理助手 |
| 学习笔记摘要 | [summarizer.py](file:///d:/AAA_MY/AAAMyGit/bili_video/src/summarizer.py) | 学习笔记整理助手 |
| 思维导图生成 | [mindmap.py](file:///d:/AAA_MY/AAAMyGit/bili_video/src/mindmap.py) | 思维导图生成助手 |

#### 2.2.2 Whisper 语音转录

本模块为本地模型，不涉及网络 API 调用。支持两种后端：

| 后端 | 库 | 适用设备 | 说明 |
|------|-----|---------|------|
| faster-whisper | `faster_whisper` | CUDA GPU | CTranslate2 加速，性能更优 |
| openai-whisper | `openai-whisper` | CPU / CUDA | 官方实现，兼容性更好 |

### 2.3 核心模块内部函数接口

#### 2.3.1 config_loader — 配置加载器

```python
# 加载配置（合并默认值 + .toml + .env）
load_config(config_path: str = "config.toml") -> dict

# 获取项目根目录绝对路径
get_project_root() -> str

# 将配置中的相对路径解析为绝对路径
resolve_path(config: dict, key: str) -> str

# 获取所有任务列表
get_tasks(config: dict) -> list

# 按名称查找任务
get_task_by_name(config: dict, name: str) -> dict | None
```

#### 2.3.2 link_parser — 链接解析器

```python
# 从文本中提取 B 站视频链接
extract_bilibili_urls(text: str) -> list[str]

# 从文本中提取所有 URL
extract_all_urls(text: str) -> list[str]

# 从文件中解析链接列表
parse_links_file(filepath: str, bilibili_only: bool = True) -> list[str]
```

#### 2.3.3 downloader — 媒体下载器

```python
# 仅下载音频 (WAV)
download_audio(url: str, output_dir: str, download_dir: str) -> dict
# 返回: {"audio_path": str, "title": str, "metadata": dict}

# 下载视频 (MP4, ≤1080p) + 提取音频
download_video(url: str, output_dir: str, download_dir: str) -> dict
# 返回: {"video_path": str, "audio_path": str, "title": str, "metadata": dict, "video_segments": list}
```

#### 2.3.4 video_splitter — 视频分段器

```python
# 获取视频时长
get_video_duration(video_path: str) -> float

# 对长视频进行分段切割（默认每段 ≤60 分钟）
split_video(video_path: str, output_dir: str, max_duration_minutes: int = 60) -> list[dict]

# 生成切割报告
save_segments_report(segments: list[dict], original_duration: float, output_dir: str) -> str

# 将 Whisper segments 时间戳适配到切割后的视频分段时间轴
filter_and_adjust_segments(original_segments: list, offset: float, seg_duration: float) -> list[dict]
```

#### 2.3.5 transcriber — 语音转录器

```python
# 统一的转录入口（自动选择 faster-whisper 或 openai-whisper）
transcribe(audio_path: str, output_dir: str, model_name: str = "medium", language: str = "zh", device: str = "cuda", compute_type: str = "auto") -> dict
# 返回: {"text": str, "segments": list, "transcript_path": str, "timestamp_md_path": str, "segments_path": str}
```

#### 2.3.6 text_cleaner — 文字清洗器

```python
# 使用 AI 添加标点符号并进行段落整理
clean_transcript_with_punctuation(config: dict, raw_text: str, output_path: str) -> str
```

#### 2.3.7 summarizer — 摘要生成器

```python
# 生成学习笔记型摘要
generate_summary(config: dict, cleaned_text: str, output_path: str) -> str
```

#### 2.3.8 mindmap — 思维导图生成器

```python
# 生成思维导图 (Markdown + HTML)
generate_mindmap(config: dict, source_text: str, output_dir: str) -> dict
# 返回: {"mindmap_md": str, "mindmap_html": str | None}
```

#### 2.3.9 screenshotter — 智能截图器

```python
class ScreenshotterInterface:
    """截图模块接口基类"""
    def __init__(self, config: dict): ...
    def process(self, video_path: str, segments_path: str, output_dir: str) -> dict:
        # 返回: {timestamp_seconds: image_relative_path}

class DefaultScreenshotter(ScreenshotterInterface):
    """基于 OpenCV + SSIM 的智能截图实现"""
    def process(self, video_path: str, segments_path: str, output_dir: str) -> dict:
        # 1. 根据 segments 确定候选时间点
        # 2. 使用 SSIM 过滤相似截图（difference_threshold 默认 0.85）
        # 3. 控制每分钟最大截图数、最小截图间隔
```

#### 2.3.10 markdown_builder — Markdown 构建器

```python
# 构建带截图的文字稿 Markdown 文件
build_transcript_with_images(segments: list, screenshots: dict, output_dir: str, title: str = "") -> str
```

#### 2.3.11 utils — 通用工具函数

```python
# 日志配置
setup_logging(log_dir: str, task_name: str = "workflow") -> logging.Logger

# 文件名处理
sanitize_filename(name: str) -> str

# 目录生成
generate_output_dirname(base_dir: str, index: int, title: str) -> str

# JSON 文件读写
load_json(filepath: str, default=None) -> list | dict
save_json(filepath: str, data): None

# 文本文件读写
read_text_file(filepath: str) -> str
write_text_file(filepath: str, content: str): None

# 时间戳转换
seconds_to_timestamp(seconds: float) -> str   # 秒 → "MM:SS" 或 "HH:MM:SS"
timestamp_to_filename(seconds: float) -> str  # 秒 → "HH_MM_SS"

# 处理状态追踪
is_url_already_processed(url: str, processed_file: str) -> bool
mark_url_processed(url: str, title: str, output_dir: str, mode: str, processed_file: str): None
mark_url_failed(url: str, mode: str, error: str, failed_file: str): None

# 目录工具
ensure_dir(path: str) -> str
```

### 2.4 配置文件接口

#### 2.4.1 config.toml 结构

配置文件使用 TOML 格式，分为全局配置 `[section]` 和任务列表 `[[tasks]]` 两种。

**`[project]` — 项目路径配置**

| 键 | 类型 | 默认值 | 说明 |
|-----|------|--------|------|
| `name` | `str` | `"bili-video-notes-workflow"` | 项目名称 |
| `output_dir` | `str` | `"outputs"` | 输出目录（相对/绝对路径） |
| `log_dir` | `str` | `"logs"` | 日志目录 |
| `temp_dir` | `str` | `"temp"` | 临时文件目录 |
| `download_dir` | `str` | `"downloads"` | 下载文件目录 |

**`[whisper]` — Whisper 转录配置**

| 键 | 类型 | 默认值 | 说明 |
|-----|------|--------|------|
| `model` | `str` | `"medium"` | 模型大小：`tiny`/`base`/`small`/`medium`/`large` |
| `language` | `str` | `"Chinese"` | 转录语言 |
| `device` | `str` | `"cuda"` | 运行设备：`cuda`/`cpu` |
| `compute_type` | `str` | `"auto"` | 计算精度（faster-whisper）：`float16`/`int8`/`auto` |

**`[deepseek]` — DeepSeek API 配置**

| 键 | 类型 | 默认值 | 说明 |
|-----|------|--------|------|
| `model` | `str` | `"deepseek-chat"` | 模型名称 |
| `base_url` | `str` | `"https://api.deepseek.com"` | API 基础 URL |
| `max_chunk_minutes` | `int` | `12` | 分块处理的每块最大对应分钟数 |
| `max_retries` | `int` | `3` | API 调用失败最大重试次数 |
| `retry_delay_seconds` | `int` | `5` | 重试等待秒数（指数递增） |
| `api_key` | `str` | — | API 密钥，**通过 `.env` 文件配置** |

**`[screenshot]` — 截图配置**

| 键 | 类型 | 默认值 | 说明 |
|-----|------|--------|------|
| `enabled` | `bool` | `false` | 是否启用截图功能 |
| `min_interval_seconds` | `int` | `5` | 截图最小间隔（秒） |
| `max_avg_per_minute` | `int` | `5` | 每分钟最大截图数 |
| `difference_threshold` | `float` | `0.85` | SSIM 相似度阈值（低于此值才视为不同画面） |

**`[[tasks]]` — 任务定义（数组，可定义多个）**

| 键 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| `name` | `str` | 是 | 任务名称（唯一标识） |
| `input_file` | `str` | 是 | 链接输入文件路径 |
| `mode` | `str` | 是 | 运行模式：`basic` / `with_images` |
| `bilibili_only` | `bool` | 否（默认 `true`） | 是否仅处理 B 站链接 |

#### 2.4.2 .env 环境变量

| 变量名 | 必填 | 说明 |
|--------|------|------|
| `DEEPSEEK_API_KEY` | 否* | DeepSeek API 密钥 |
| `DEEPSEEK_BASE_URL` | 否 | 自定义 API 代理地址 |

> *注：若未配置 API Key，AI 相关功能（标点补全、摘要、思维导图）将自动跳过。

---

## 3. 功能说明

### 3.1 链接解析模块

**文件**：[src/link_parser.py](file:///d:/AAA_MY/AAAMyGit/bili_video/src/link_parser.py)

**功能名称**：B站视频链接自动提取

**实现逻辑**：

1. 读取链接文件（`links.txt` 或 `links_with_images.txt`）
2. 按行解析，跳过空行和 `#` 注释行
3. 使用正则表达式匹配 B站链接，支持三种格式：
   - `https://(www.)?bilibili.com/video/av{id}` 或 `BV{id}`
   - `https://b23.tv/{short_code}` 短链
   - `https://(www.)?bilibili.com/bangumi/play/ep{id}` 或 `ss{id}` 番剧
4. 自动去重和清理尾部标点

**核心算法**：正则匹配 + 去重（`BILIBILI_URL_PATTERNS` 列表，参见 [link_parser.py:L6-L21](file:///d:/AAA_MY/AAAMyGit/bili_video/src/link_parser.py#L6-L21)）

**关联功能**：为主流程提供待处理的视频 URL 列表。

---

### 3.2 媒体下载模块

**文件**：[src/downloader.py](file:///d:/AAA_MY/AAAMyGit/bili_video/src/downloader.py)

**功能名称**：B站视频/音频自动下载

**实现逻辑**：

1. 检测 ffmpeg 硬件加速支持（CUDA/QSV）
2. 根据模式选择下载策略：

   **`download_audio`（Basic 模式）**：
   - 使用 `yt-dlp` 仅下载音频，输出格式为 WAV（16kHz 单声道）
   - 下载超时 30 分钟

   **`download_video`（With-Images 模式）**：
   - 使用 `yt-dlp` 下载最佳视频+音频，合并为 MP4（限制最高 1080p）
   - 下载超时 60 分钟
   - 下载完成后自动：
     - 提取音频为 WAV（通过 ffmpeg）
     - 调用 `video_splitter.split_video()` 进行分段

3. 解析 yt-dlp 的 `.info.json` 元数据

**业务规则**：
- 仅下载不超过 1080p 的视频，避免文件过大
- 音频统一转换为 16kHz 单声道 PCM WAV（Whisper 最佳输入格式）
- 自动检测 GPU 硬件加速并启用

---

### 3.3 视频分段模块

**文件**：[src/video_splitter.py](file:///d:/AAA_MY/AAAMyGit/bili_video/src/video_splitter.py)

**功能名称**：长视频自动分段切割

**实现逻辑**：

1. 使用 `ffprobe` 获取视频总时长
2. 如果时长 > 60 分钟，使用 `ffmpeg segment` 切割为多段
3. 切割方式：`ffmpeg -c copy`（流拷贝，无转码，速度快）
4. 为每个分段记录：路径、起始偏移、时长、序号

**核心函数**：

| 函数 | 说明 |
|------|------|
| `split_video()` | 主切割函数，返回分段信息列表 |
| `filter_and_adjust_segments()` | 将 Whisper 转录的时间戳适配到分段时间轴 |
| `save_segments_report()` | 生成切割报告 Markdown |
| `get_video_duration()` | 获取视频时长 |

**关联功能**：与 `downloader`（调用方）、`screenshotter`（分段截图）、`transcriber`（时间戳适配）协同工作。

---

### 3.4 语音转录模块

**文件**：[src/transcriber.py](file:///d:/AAA_MY/AAAMyGit/bili_video/src/transcriber.py)

**功能名称**：Whisper 语音转文字

**实现逻辑**：

1. **自动后端选择**：
   - 若 `faster-whisper` 已安装且设备为 CUDA → 使用 faster-whisper
   - 否则 → 回退使用 `openai-whisper`

2. **faster-whisper 特性**：
   - CTranslate2 GPU 加速
   - VAD（语音活动检测）过滤静音（`min_silence_duration_ms=500`）
   - word-level 时间戳

3. **openai-whisper 特性**：
   - 标准 Whisper 转录
   - word-level 时间戳

4. **后处理**：
   - 使用 OpenCC 将繁体中文转为简体
   - 保存三个输出文件：
     - `transcript.txt` — 纯文本
     - `transcript_with_timestamps.md` — 带时间戳的 Markdown 文字稿
     - `segments.json` — 结构化分段数据

**核心规则**：
- 转录语言：`"Chinese"` 映射为 `"zh"`
- 音频格式要求：WAV，16kHz 采样率，单声道

---

### 3.5 文字清洗模块

**文件**：[src/text_cleaner.py](file:///d:/AAA_MY/AAAMyGit/bili_video/src/text_cleaner.py)

**功能名称**：AI 标点补全与段落整理

**实现逻辑**：

1. 将无标点的转录原文按 `max_chunk_chars`（= `max_chunk_minutes * 800`）分块
2. 分块策略：按自然段落（`\n`）分割，尽量完整保留段落
3. 逐块调用 DeepSeek API，使用以下 System Prompt：
   - 添加标点符号（句号、逗号、问号、感叹号等）
   - 根据语义进行合理分段
   - 保持原文措辞不变
4. 合并所有分块结果

**关联功能**：输出是 `summarizer` 和 `mindmap` 的输入。

---

### 3.6 摘要生成模块

**文件**：[src/summarizer.py](file:///d:/AAA_MY/AAAMyGit/bili_video/src/summarizer.py)

**功能名称**：AI 学习笔记摘要生成

**实现逻辑**：

1. 如果文本 > `max_chunk_chars`：
   - 分块生成摘要（每块 → 要点摘要）
   - 二次整合：将所有要点摘要合并为完整笔记
2. 如果文本较短：直接生成完整笔记
3. System Prompt 要求：
   - Markdown 格式
   - 核心内容提炼 + 要点归纳
   - 保留代码/公式
   - 末尾附「关键要点」小节（3-7 个 takeaway）

---

### 3.7 思维导图生成模块

**文件**：[src/mindmap.py](file:///d:/AAA_MY/AAAMyGit/bili_video/src/mindmap.py)

**功能名称**：AI 思维导图生成

**实现逻辑**：

1. 以文字稿为输入，调用 DeepSeek API
2. System Prompt 要求输出层级结构（`#`/`##`/`###`/`-`）
3. 输出两种格式：
   - **Markdown 文件**（`mindmap.md`）：结构化思维导图
   - **HTML 文件**（`mindmap.html`）：可浏览器查看的可视化思维导图
     - 通过简单的 Markdown→HTML 转换器渲染
     - 内置 CSS 样式，美观清晰

**渲染规则**（参见 [mindmap.py:L120-L160](file:///d:/AAA_MY/AAAMyGit/bili_video/src/mindmap.py#L120-L160)）：

| Markdown 标记 | HTML 标签 | 说明 |
|---------------|-----------|------|
| `# text` | `<h1>` | 中心主题 |
| `## text` | `<h2>` | 一级分支 |
| `### text` | `<h3>` | 二级分支 |
| `- text` | `<ul><li>` | 具体要点 |

**关联功能**：输入来自 `text_cleaner` 的处理结果。

---

### 3.8 智能截图模块

**文件**：[src/screenshotter.py](file:///d:/AAA_MY/AAAMyGit/bili_video/src/screenshotter.py)

**功能名称**：视频关键帧智能截图

**设计模式**：策略模式（Strategy Pattern）

```
ScreenshotterInterface (抽象基类)
    └── DefaultScreenshotter (具体实现)
```

**实现逻辑**（`DefaultScreenshotter.process()`）：

1. 读取 `segments.json`，生成候选截图时间点：
   - 长语义段（≥ 15 秒）：取中间时刻
   - 短语义段：取起始时刻
2. 使用 OpenCV 逐帧读取视频
3. **SSIM 去重判断**：
   - 将当前帧灰度图缩放到 160×90
   - 与上一张已截图的帧计算 SSIM（结构相似度）
   - 若 SSIM > `difference_threshold`（默认 0.85），视为相似画面，跳过
4. **频率控制**：
   - 最小截图间隔 ≥ `min_interval_seconds`（默认 5 秒）
   - 每分钟截图数 ≤ `max_avg_per_minute`（默认 5 张）
5. 输出 JPEG 图片（质量 85%），文件名格式：`HH_MM_SS.jpg`

**核心算法**：SSIM (Structural Similarity Index Measure) — 结构相似性度量，用于判断两张图片是否"看起来相似"。

---

### 3.9 Markdown 构建模块

**文件**：[src/markdown_builder.py](file:///d:/AAA_MY/AAAMyGit/bili_video/src/markdown_builder.py)

**功能名称**：图文笔记整合

**实现逻辑**：

1. 遍历 Whisper segments（语义段落）
2. 为每个 segment 输出时间戳 + 文字
3. 将截图按时间戳匹配到对应的 segment 中
4. 输出 `transcript_with_images.md`

**匹配规则**：截图的 `timestamp` 落在 segment 的 `[start, end]` 区间内即追加到该 segment 下方。

---

### 3.10 配置管理模块

**文件**：[src/config_loader.py](file:///d:/AAA_MY/AAAMyGit/bili_video/src/config_loader.py)

**功能名称**：多层级配置加载

**实现逻辑**：

1. 内置 `DEFAULT_CONFIG`（硬编码默认值）
2. 读取 `config.toml`，深度合并覆盖默认值
3. 从 `.env` 文件加载环境变量（`DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL`）
4. 路径自动解析：相对路径 → 基于项目根目录的绝对路径

**合并策略**：深度合并（Deep Merge）— 嵌套字典逐层覆盖，而非整体替换。

---

### 3.11 工具函数模块

**文件**：[src/utils.py](file:///d:/AAA_MY/AAAMyGit/bili_video/src/utils.py)

| 功能 | 函数 | 说明 |
|------|------|------|
| 日志配置 | `setup_logging()` | 文件 + 控制台双通道，自动按任务命名 |
| 文件名清理 | `sanitize_filename()` | 移除非法字符，限制长度 ≤ 120 |
| 输出目录生成 | `generate_output_dirname()` | 格式：`{index:03d}_{sanitized_title}` |
| JSON 读写 | `load_json()` / `save_json()` | UTF-8，`ensure_ascii=False` |
| 时间戳转换 | `seconds_to_timestamp()` | `MM:SS` 或 `HH:MM:SS` |
| 时间戳文件名 | `timestamp_to_filename()` | `HH_MM_SS` |
| 处理状态追踪 | `is_url_already_processed()` / `mark_url_processed()` / `mark_url_failed()` | 断点续跑支持 |

---

## 4. 使用手册

### 4.1 环境配置要求

#### 4.1.1 硬件要求

| 项目 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | x86_64 架构 | 4 核以上 |
| GPU | 无（可纯 CPU 运行） | NVIDIA GPU（CUDA 支持），≥ 4GB 显存 |
| 内存 | 8 GB | 16 GB+ |
| 磁盘 | 10 GB 可用 | SSD，50 GB+ |

#### 4.1.2 软件依赖

| 软件 | 版本要求 | 安装方式 |
|------|---------|---------|
| Python | ≥ 3.10 | [python.org](https://python.org) |
| ffmpeg + ffprobe | 最新稳定版 | 添加到系统 PATH |
| yt-dlp | 最新版 | `pip install yt-dlp` |

> **Windows 特别注意**：ffmpeg 需手动下载并将 `bin/` 目录添加到系统 PATH 环境变量。

#### 4.1.3 Python 依赖

参见 [requirements.txt](file:///d:/AAA_MY/AAAMyGit/bili_video/requirements.txt)：

```
faster-whisper>=1.0.0
openai-whisper>=20231117
openai>=1.0.0
python-dotenv>=1.0.0
toml>=0.10.0
opencc>=1.1.0
opencv-python>=4.8.0
scikit-image>=0.22.0
```

### 4.2 部署步骤

#### Step 1：克隆/下载项目

```bash
cd d:\AAA_MY\AAAMyGit\bili_video
```

#### Step 2：创建虚拟环境（推荐）

```bash
python -m venv venv
.\venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/Mac
```

#### Step 3：安装 Python 依赖

```bash
pip install -r requirements.txt
pip install yt-dlp
```

#### Step 4：配置环境变量

复制 `.env.example` 为 `.env`：

```bash
copy .env.example .env
```

编辑 `.env`，填入 DeepSeek API Key：

```
DEEPSEEK_API_KEY=sk-your-api-key-here
```

#### Step 5：创建配置文件

复制 `config.example.toml` 为 `config.toml`：

```bash
copy config.example.toml config.toml
```

根据需求编辑 `config.toml`（具体配置项参见 [2.4 配置文件接口](#24-配置文件接口)）。

#### Step 6：准备链接文件

编辑 `links.txt`，每行一个 B站视频链接：

```
# 示例
https://www.bilibili.com/video/BV1xx411c7mD
https://b23.tv/xxxxxx
```

对于需要截图的视频，编辑 `links_with_images.txt`。

### 4.3 启动方法

#### 4.3.1 Basic 模式（仅音频+笔记）

```bash
# 方式A：使用配置文件中的任务
python main.py --task basic_test

# 方式B：直接指定
python main.py --input links.txt --mode basic
```

输出产物：
- `transcript.txt` — 纯文字稿
- `transcript_with_timestamps.md` — 带时间戳文字稿
- `transcript_with_punct.txt` — AI 标点补全后的文本
- `summary.md` — AI 学习笔记摘要
- `mindmap.md` + `mindmap.html` — 思维导图

#### 4.3.2 With-Images 模式（视频+截图+笔记）

```bash
python main.py --task with_images_test
# 或
python main.py --input links_with_images.txt --mode with_images
```

额外输出产物：
- `transcript_with_images.md` — 带截图的 Markdown 笔记
- `images/` — 截图图片目录
- `video_segments_report.md` — 视频切割报告（长视频）

#### 4.3.3 运行所有任务

```bash
python main.py
```

将依次执行 `config.toml` 中 `[[tasks]]` 定义的所有任务。

### 4.4 日常操作流程

```
1. 收集 B站视频链接
   │
   ▼
2. 将链接粘贴到 links.txt / links_with_images.txt
   │
   ▼
3. 运行 python main.py --task basic_test
   │
   ▼
4. 检查 outputs/ 目录下的结果文件
   │
   ▼
5. 查看 summary.md 学习笔记、mindmap.html 思维导图
```

**断点续跑**：程序会自动记录已处理的 URL 到 `processed.json`，失败的记录到 `failed.json`。再次运行时自动跳过已处理的链接。

**查看失败链接**：

```bash
# 查看 failed.json 了解失败原因
type failed.json
```

### 4.5 常见问题排查

#### Q1：yt-dlp 下载失败

**现象**：`RuntimeError: 下载失败`

**排查**：
1. 确认 yt-dlp 已安装：`yt-dlp --version`
2. 手动测试下载：`yt-dlp <视频URL>`
3. 如提示 "unable to download webpage"，可能是 IP 被限制，尝试使用代理或 cookie

#### Q2：Whisper 转录失败 / OOM

**现象**：内存溢出或 CUDA 错误

**解决**：
1. 减少模型大小：`config.toml` 中 `whisper.model = "small"` 或 `"base"`
2. 使用 CPU：`whisper.device = "cpu"`
3. 确保有足够显存（medium 模型约需 3GB，large 约需 6GB）

#### Q3：DeepSeek API 调用失败

**现象**：日志显示 `DeepSeek API 调用最终失败`

**排查**：
1. 检查 `.env` 中 `DEEPSEEK_API_KEY` 是否正确
2. 检查网络能否访问 `https://api.deepseek.com`
3. 检查 API 账户余额

**降级行为**：即使 API 不可用，转录仍可正常完成，仅跳过 AI 处理步骤。

#### Q4：ffmpeg 不可用

**现象**：`FileNotFoundError` 或 ffmpeg 相关错误

**解决**：
1. 确认 ffmpeg 已安装：`ffmpeg -version`
2. Windows：将 ffmpeg `bin/` 目录添加到系统 PATH

#### Q5：处理重复的视频

**现象**：同一 URL 每次都要重新处理

**解决**：检查 `processed.json` 是否存在且可写。程序会自动记录已处理链接。

#### Q6：截图功能不生效

**原因**：需同时满足以下条件才启用截图：
1. 运行模式为 `with_images`
2. 或 `screenshot.enabled = true`
3. 已安装 `opencv-python` 和 `scikit-image`

---

## 5. 数据结构说明

### 5.1 核心数据模型

#### 5.1.1 Whisper Segment

转录片段（segments.json），每个 segment 对应一段连续的语音。

```python
{
    "start": float,    # 起始时间（秒）
    "end": float,      # 结束时间（秒）
    "text": str        # 转录文本（已繁转简）
}
```

#### 5.1.2 Video Segment

视频分段信息。

```python
{
    "path": str,           # 分段文件路径
    "start_offset": float, # 在原视频中的起始偏移（秒）
    "duration": float,     # 分段时长（秒）
    "index": int           # 分段序号（从 1 开始）
}
```

#### 5.1.3 Video Metadata

视频元数据（metadata.json）。

```python
{
    "title": str,          # 视频标题
    "duration": float,     # 总时长（秒）
    "uploader": str,       # UP主名称
    "upload_date": str,    # 上传日期
    "description": str,    # 视频简介
    "webpage_url": str     # 原始URL
}
```

#### 5.1.4 Processed Record

已处理记录（processed.json）。

```python
{
    "url": str,            # 原始视频URL
    "title": str,          # 视频标题
    "output_dir": str,     # 输出目录路径
    "mode": str,           # 处理模式 (basic / with_images)
    "processed_at": str    # 处理时间 (ISO 8601)
}
```

#### 5.1.5 Failed Record

失败记录（failed.json）。

```python
{
    "url": str,            # 原始视频URL
    "mode": str,           # 运行模式
    "error": str,          # 错误信息
    "failed_at": str       # 失败时间 (ISO 8601)
}
```

#### 5.1.6 Screenshot Mapping

截图映射（内存中），用于构建图文笔记。

```python
{
    timestamp_seconds: str  # e.g. {125.5: "images/00_02_05.jpg", ...}
}
```

#### 5.1.7 Transcriber Output

转录结果（函数返回值）。

```python
{
    "text": str,                       # 完整纯文本
    "segments": list[WhisperSegment],  # 分段列表
    "transcript_path": str,            # 纯文本文件路径
    "timestamp_md_path": str,          # 带时间戳 Markdown 路径
    "segments_path": str               # segments JSON 路径
}
```

#### 5.1.8 Downloader Result

下载结果（函数返回值）。

```python
# download_audio 返回：
{
    "audio_path": str,
    "title": str,
    "metadata": dict   # VideoMetadata
}

# download_video 返回：
{
    "video_path": str,
    "audio_path": str,
    "title": str,
    "metadata": dict,           # VideoMetadata
    "video_segments": list[dict] # VideoSegment 列表
}
```

### 5.2 文件存储结构

单次处理的输出目录结构：

```
outputs/
└── 001_视频标题/                    # 每个视频一个独立目录
    ├── audio.wav                    # 提取的音频文件
    ├── segments.json                # Whisper 转录分段数据
    ├── metadata.json                # 视频元数据
    ├── video_part_000.mp4           # 视频分段文件（长视频）
    ├── video_part_001.mp4
    ├── segments_part_000.json       # 适配后的分段数据
    ├── segment_000/                 # 每个分段的截图目录
    │   └── images/
    │       ├── 00_00_05.jpg
    │       └── 00_01_30.jpg
    └── results/                     # 最终结果输出
        ├── transcript.txt           # 纯文字稿
        ├── transcript_with_timestamps.md  # 带时间戳文字稿
        ├── transcript_with_punct.txt      # AI标点补全文本
        ├── summary.md               # 学习笔记摘要
        ├── mindmap.md               # 思维导图 (Markdown)
        ├── mindmap.html             # 思维导图 (HTML)
        ├── transcript_with_images.md # 图文并茂笔记
        └── video_segments_report.md  # 视频切割报告
```

### 5.3 持久化数据格式

| 文件 | 格式 | 内容 | 读写模块 |
|------|------|------|---------|
| `config.toml` | TOML | 项目全局配置 + 任务列表 | `config_loader` |
| `.env` | 环境变量 | API 密钥 | `python-dotenv` |
| `links.txt` | 纯文本 | 待处理链接（每行一个） | `link_parser` |
| `processed.json` | JSON Array | 已处理 URL 记录 | `utils` |
| `failed.json` | JSON Array | 失败 URL 记录 | `utils` |
| `segments.json` | JSON Array | Whisper 转录分段 | `transcriber` |
| `metadata.json` | JSON Object | 视频元数据 | `downloader` |
| `*.md` | Markdown | 各类笔记输出 | 各模块 |
| `*.html` | HTML | 思维导图可视化 | `mindmap` |
| `*.jpg` | JPEG | 视频截图 | `screenshotter` |
| `*.wav` | WAV (PCM 16kHz) | 音频文件 | `downloader` |
| `*.log` | 纯文本 | 运行日志 | `utils` |

---

## 6. 关键业务流程

### 6.1 整体处理流程

```
                    ┌──────────────────┐
                    │   main() 入口    │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │ 解析 CLI 参数    │
                    │ 加载 config.toml │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │ 确定任务配置     │
                    │ (task/mode/input)│
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │ 设置日志系统     │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │ 读取链接文件     │
                    │ 提取有效URL列表  │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
              ┌────►│ 遍历 URL 列表    │
              │     └────────┬─────────┘
              │              │
              │     ┌────────▼─────────┐
              │     │ 是否已处理？     │
              │     └────┬───────┬─────┘
              │          │ Yes   │ No
              │          ▼       │
              │     ┌────────┐   │
              │     │ 跳过   │   │
              │     └────────┘   │
              │                  │
              │     ┌────────────▼─────────┐
              │     │ process_single_video()│ ───► 参见 6.2/6.3
              │     └────────────┬─────────┘
              │                  │
              │     ┌────────────▼─────────┐
              │     │ 记录成功/失败状态    │
              │     └────────────┬─────────┘
              │                  │
              └──────────────────┘  (循环)
                             │
                    ┌────────▼─────────┐
                    │ 输出任务统计报告 │
                    └──────────────────┘
```

### 6.2 Basic 模式流程

```
process_single_video() [mode=basic]
│
├─► downloader.download_audio()
│   └─► yt-dlp --extract-audio → WAV
│
├─► transcriber.transcribe()
│   ├─► faster-whisper / openai-whisper
│   ├─► OpenCC 繁→简
│   └─► 输出: transcript.txt, segments.json, transcript_with_timestamps.md
│
├─► text_cleaner.clean_transcript_with_punctuation()
│   ├─► 按 max_chunk_chars 分块
│   ├─► DeepSeek API: 标点补全 + 分段
│   └─► 输出: transcript_with_punct.txt
│
├─► summarizer.generate_summary()
│   ├─► 分块策略（长文本）
│   ├─► DeepSeek API: 生成学习笔记
│   └─► 输出: summary.md
│
├─► mindmap.generate_mindmap()
│   ├─► DeepSeek API: 生成结构化大纲
│   ├─► Markdown → HTML 渲染
│   └─► 输出: mindmap.md, mindmap.html
│
└─► utils.mark_url_processed()
    └─► 更新 processed.json
```

### 6.3 With-Images 模式流程

```
process_single_video() [mode=with_images]
│
├─► downloader.download_video()
│   ├─► yt-dlp 下载 MP4 (≤1080p)
│   ├─► ffmpeg 提取音频 → WAV
│   └─► video_splitter.split_video() → video_segments[]
│
├─► transcriber.transcribe()
│   └─► ... (同 Basic 模式)
│
├─► text_cleaner.clean_transcript_with_punctuation()
│   └─► ... (同 Basic 模式)
│
├─► summarizer.generate_summary()
│   └─► ... (同 Basic 模式)
│
├─► mindmap.generate_mindmap()
│   └─► ... (同 Basic 模式)
│
├─► 截图处理（遍历 video_segments）:
│   for seg in video_segments:
│   ├─► video_splitter.filter_and_adjust_segments()
│   │   └─► 将转录时间戳适配到分段时间轴
│   ├─► screenshotter.DefaultScreenshotter.process()
│   │   ├─► 计算候选截图时间点
│   │   ├─► OpenCV 逐帧读取
│   │   ├─► SSIM 相似度去重
│   │   └─► 频率控制 → 输出 JPEG
│   └─► 收集截图映射 {global_ts: relative_path}
│
├─► markdown_builder.build_transcript_with_images()
│   └─► 将截图匹配到对应 segment → transcript_with_images.md
│
├─► video_splitter.save_segments_report()
│   └─► 输出 video_segments_report.md
│
└─► utils.mark_url_processed()
```

### 6.4 断点续跑机制

```
遍历 URL 列表
    │
    ├─► 读取 processed.json
    ├─► 检查 current_url 是否在 processed 中
    │
    ├─► 已存在 → 跳过 (skip_count++)
    │
    └─► 不存在 → 执行处理流程
                  │
                  ├─► 成功 → 写入 processed.json (append)
                  │
                  └─► 失败 → 写入 failed.json (append)
```

**设计要点**：
- `processed.json` 和 `failed.json` 均为追加写入（非覆盖）
- 每次运行开始时加载完整记录，用于去重判断
- 支持多次运行累积处理，无需手动清理

---

## 7. Web 平台

### 7.1 概述

自 v1.4.0 起，项目新增基于 **FastAPI + React** 的 Web 平台，提供图形化操作界面替代命令行交互。

**核心特性**：
- **任务管理**：通过 Web UI 提交视频链接、查看进度、管理历史
- **实时进度**：WebSocket 推送各处理阶段状态
- **笔记展示**：摘要、思维导图（HTML 可视化）、图文笔记的在线查看
- **配置管理**：在线编辑 `config.toml` 各项参数，测试 API Key 有效性
- **API 契约层**：基于 OpenAPI schema + openapi-typescript 的前后端类型一致保障

### 7.2 技术栈

| 层 | 技术 | 说明 |
|-----|------|------|
| **后端** | FastAPI + Pydantic v2 | REST API + WebSocket |
| **前端** | React 19 + TypeScript 6 + Vite 8 + Tailwind CSS 4 | SPA 单页应用 |
| **契约** | OpenAPI 3.1 + openapi-typescript 7 | 自动类型生成 |
| **部署** | Docker (CPU/GPU) + uvicorn | 前后端同容器托管 |

### 7.3 快速启动

```bash
# 开发模式（前后端分离）
python -m web.main              # 启动后端 :8000
cd frontend && npm run dev      # 启动前端 :5173 (含 Vite proxy)

# 生产模式（前后端一体化）
cd frontend && npm run build    # 构建前端 → dist/
python -m web.main              # 启动后端 → http://localhost:8000
```

### 7.4 相关文档

| 文档 | 内容 |
|------|------|
| [API.md](docs/API.md) | 完整 REST API + WebSocket 参考（15+ 端点） |
| [WEB_ARCHITECTURE.md](docs/WEB_ARCHITECTURE.md) | Web 平台架构设计（组件树、数据流、部署拓扑） |

---

## 8. 已知问题与限制

本章节记录当前版本（v1.4.0）中已验证的已知问题、限制和需要注意的边界条件。这些问题不影响核心功能的正常使用，但部署者和使用者应当知晓。

### 8.1 部署就绪性问题

#### 8.1.1 `config.toml` 需用户自行创建

**现状**：项目仅提供 [config.example.toml](file:///d:/AAA_MY/AAAMyGit/bili_video/config.example.toml) 模板，不包含实际运行用的 `config.toml`（该文件在 `.gitignore` 中排除）。

**影响**：
- 直接运行 `python main.py` 时，`[[tasks]]` 数组为空
- 程序会打印 `"[INFO] config.toml 中未定义任务"` 提示并退出

**解决**：参考 README 中的"5 分钟快速部署"步骤，复制模板并编辑。

#### 8.1.2 `.env` 需用户自行创建

**现状**：仅提供空的 `.env.example` 模板。

**影响**：
- `DEEPSEEK_API_KEY` 为空字符串
- 所有 AI 功能（标点补全 → [text_cleaner.py](file:///d:/AAA_MY/AAAMyGit/bili_video/src/text_cleaner.py)、摘要 → [summarizer.py](file:///d:/AAA_MY/AAAMyGit/bili_video/src/summarizer.py)、思维导图 → [mindmap.py](file:///d:/AAA_MY/AAAMyGit/bili_video/src/mindmap.py)）会走 fallback 逻辑，输出原文或跳过

**解决**：创建 `.env` 文件并填入有效的 `DEEPSEEK_API_KEY`。

#### 8.1.3 `requirements.txt` 未声明 `yt-dlp`

**现状**：[requirements.txt](file:///d:/AAA_MY/AAAMyGit/bili_video/requirements.txt) 中不包含 `yt-dlp` 依赖声明。

**源码依赖位置**：
- [downloader.py:L49](file:///d:/AAA_MY/AAAMyGit/bili_video/src/downloader.py#L49) — `download_audio()` 调用 `subprocess.run(["yt-dlp", ...])`
- [downloader.py:L114](file:///d:/AAA_MY/AAAMyGit/bili_video/src/downloader.py#L114) — `download_video()` 调用 `subprocess.run(["yt-dlp", ...])`

**影响**：在新环境中仅执行 `pip install -r requirements.txt` 后运行程序，下载阶段会因找不到 `yt-dlp` 命令而报 `FileNotFoundError`。

**解决**：手动执行 `pip install yt-dlp`，部署文档已明确说明。

#### 8.1.4 `ffmpeg` / `ffprobe` 为外部系统依赖

**现状**：以下模块通过 `subprocess` 调用系统安装的 ffmpeg/ffprobe：

| 模块 | 位置 | 功能 |
|------|------|------|
| `downloader._extract_audio_from_video()` | [downloader.py:L218](file:///d:/AAA_MY/AAAMyGit/bili_video/src/downloader.py#L218) | 从视频提取 WAV 音频 |
| `downloader._check_ffmpeg_gpu()` | [downloader.py:L20-L21](file:///d:/AAA_MY/AAAMyGit/bili_video/src/downloader.py#L20-L21) | 检测 GPU 硬件加速 |
| `video_splitter.get_video_duration()` | [video_splitter.py:L12](file:///d:/AAA_MY/AAAMyGit/bili_video/src/video_splitter.py#L12) | 获取视频时长 |
| `video_splitter.split_video()` | [video_splitter.py:L69](file:///d:/AAA_MY/AAAMyGit/bili_video/src/video_splitter.py#L69) | 长视频分段切割 |

**影响**：
- `basic` 模式：不受影响（仅下载音频，不调用 ffmpeg）
- `with_images` 模式：ffmpeg 缺失会导致音频提取返回空字符串、视频切割回退到单段原始视频（有 fallback 容错，不会崩溃）

**解决**：从 [ffmpeg.org](https://ffmpeg.org) 下载，将 `bin/` 目录添加到系统 PATH。

### 8.2 视频下载相关限制

#### 8.2.1 `basic` 模式不下载完整视频

**源码位置**：[main.py:L39-L42](file:///d:/AAA_MY/AAAMyGit/bili_video/main.py#L39-L42)

```python
if with_images or screenshot_enabled:
    result = downloader.download_video(url, "", download_dir)
else:
    result = downloader.download_audio(url, "", download_dir)
```

**条件判定链**：

| 条件 | `basic` 模式 | `basic` + `screenshot.enabled=true` | `with_images` 模式 |
|------|:--:|:--:|:--:|
| `with_images` | `False` | `False` | `True` |
| `screenshot_enabled` | `False`（默认） | `True` | —（短路） |
| 最终调用 | `download_audio()` | `download_video()` | `download_video()` |
| 是否下载视频文件 | ❌ | ✅ | ✅ |

**影响**：若需求明确要求"下载对应视频内容"，默认 `basic` 模式不满足。`basic` 模式仅下载音频（WAV），不产生视频文件。

**结论**：项目具备下载视频的能力（`download_video()` 函数完整可用），但默认工作流设计为音频优先。

#### 8.2.2 下载后输出目录路径时机瑕疵

**源码位置**：[main.py:L40](file:///d:/AAA_MY/AAAMyGit/bili_video/main.py#L40) 和 [main.py:L42](file:///d:/AAA_MY/AAAMyGit/bili_video/main.py#L42)

**时序问题**：

```
main.py 调用                             downloader 内部操作
─────────────────────────────────        ─────────────────────────────────
download_video(url, "", download_dir)    → metadata.json 写到 CWD
                                         → _extract_audio_from_video(video_path, "")
                                           audio.wav 写到 CWD
                                         → split_video(video_path, "")
                                           视频分段文件写到 CWD

[完成下载后]
main.py:L49 创建 output_dir              ← 此时才确定正确的输出路径
main.py:L52  copy audio → output_dir    ← 音频有事后 copy 补救
```

**影响**：
- 音频文件：有 `shutil.copy2()` 补救逻辑，最终会出现在正确的 `output_dir` 中
- `metadata.json`：无事后搬迁逻辑，遗留在当前工作目录
- 视频切割分段文件：无事后搬迁逻辑，遗留在当前工作目录
- `download_audio()` 同理，`metadata.json` 也面临相同问题

**风险评估**：低 — 不影响核心输出（转录、笔记等均在正确的 `output_dir` 中），但产物分布不够整洁。

#### 8.2.3 B站登录态 / Cookie / 风控场景未处理

**源码位置**：[downloader.py:L49-L58](file:///d:/AAA_MY/AAAMyGit/bili_video/src/downloader.py#L49-L58) 和 [downloader.py:L114-L122](file:///d:/AAA_MY/AAAMyGit/bili_video/src/downloader.py#L114-L122)

**当前 yt-dlp 参数**（`download_audio` 和 `download_video` 均相同）：
```
yt-dlp
  -f <format>              # 格式选择
  -o <template>            # 输出路径模板
  --print after_move:filepath
  --write-info-json        # 写元数据
  --no-playlist            # 不下载播放列表
  <url>
```

**缺少的能力**：

| 缺失项 | 说明 |
|--------|------|
| `--cookies <file>` | 无法使用 cookie 文件绕过登录 |
| `--cookies-from-browser` | 无法从浏览器导入 cookie |
| `--username` / `--password` | 无法使用账号密码登录 |
| 代理配置 | 无代理支持，某些网络环境可能无法访问 B站 |
| 自定义 Header | 无法添加自定义请求头规避风控 |

**影响**：
- 公开视频：大概率正常工作
- 需要登录的视频（会员专享、年龄验证、地区限制）：下载必然失败
- 风控严格的时段/IP：可能触发验证码导致下载失败

### 8.3 功能边界说明

#### 8.3.1 文字清洗模块不包含"语句通顺度优化"

**源码位置**：[text_cleaner.py:L61-L68](file:///d:/AAA_MY/AAAMyGit/bili_video/src/text_cleaner.py#L61-L68)

**System Prompt 核心约束**：
```
3. 保持原文内容不变，只添加标点和分段
5. 不要修改原文的措辞和用词
```

**影响**：该模块的实际能力是 **标点补全 + 段落整理**，不包含语句通顺度优化。Whisper 转录中常见的口语化表达、语序不通、重复词等问题不会被修正。

**期望与实际对比**：

| 期望 | 实际 | 满足？ |
|------|------|:--:|
| 添加标点符号 | ✅ 支持 | ✅ |
| 按语义分段 | ✅ 支持 | ✅ |
| 修正不通顺语句 | ❌ prompt 明确禁止修改措辞 | ❌ |
| 优化口语化表达 | ❌ prompt 明确禁止修改措辞 | ❌ |

#### 8.3.2 AI 功能为可选项，非强依赖

以下功能依赖 DeepSeek API，未配置 API Key 时自动降级：
- 标点补全 → 返回原文
- 学习笔记摘要 → 输出空模板
- 思维导图生成 → 输出空模板

核心转录功能（Whisper）始终可用，不依赖任何外部 API。

#### 8.3.3 视频切割仅限 `with_images` 模式

`video_splitter` 模块仅在 `download_video()` 内部被调用（[downloader.py:L165](file:///d:/AAA_MY/AAAMyGit/bili_video/src/downloader.py#L165)），而 `download_video()` 仅在 `with_images` 或截图启用时触发。`basic` 模式不会执行视频切割。

#### 8.3.4 Windows 路径兼容性

项目中使用了 `os.path.join()` 进行路径拼接，同时在某些位置使用 `/` 分隔符。跨平台部署时需注意路径分隔符差异，Linux/Mac 环境应无问题。

---

## 9. 版本历史

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)（Semantic Versioning），
变更日志格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

| 版本 | 日期 | 类型 | 说明 |
|------|------|------|------|
| **v1.4.0** | 2026-05-25 | MINOR | Web 平台正式上线：FastAPI REST API + WebSocket + React 19 SPA + OpenAPI 契约层 + 配置在线管理 |
| **v1.3.0** | 2026-05-23 | MINOR | 学习单元驱动截图策略 (LearningScreenshotter)，五维度帧评分系统 |
| **v1.2.0** | 2026-05-22 | MINOR | Docker 容器化支持 (CPU + GPU 双版本) |
| **v1.1.0** | 2026-05-22 | MINOR | Bug 修复与健壮性增强：修复 CUDA DLL 缺失崩溃、API Key 占位符崩溃、OpenCV 中文路径截图写入失败、断点续跑模式互斥问题；新增 API Key 有效性校验 |
| **v1.0.0** | 2026-05-20 | MAJOR | 初始版本。完整的 B站视频→笔记端到端流水线 |

完整变更记录详见 [CHANGELOG.md](CHANGELOG.md)。

---

## 10. 贡献指南

### 代码规范

- 遵循 Python PEP 8 代码风格
- 不添加无意义的注释，代码应自解释
- 使用 `logging` 模块进行日志记录，不使用 `print()`
- 所有公开函数需要类型标注（type hints）

### 提交前检查

```bash
# 运行代码质量检查
python _check.py
```

该脚本执行：
1. **pyright** 全项目静态类型检查
2. **AST** 编译语法检查

### 模块扩展指南

**添加新的截图策略**：
继承 `ScreenshotterInterface`（[screenshotter.py](file:///d:/AAA_MY/AAAMyGit/bili_video/src/screenshotter.py)），实现 `process()` 方法即可。

**添加新的 AI 后端**：
修改 `_create_client()` 函数，支持其他 OpenAI 兼容 API（如 OpenAI、Azure OpenAI、本地 LLM 等），修改 `config.toml` 中的 `base_url` 即可切换。

**添加新的转录后端**：
在 [transcriber.py](file:///d:/AAA_MY/AAAMyGit/bili_video/src/transcriber.py) 中添加新的 `_transcribe_xxx()` 函数，在 `transcribe()` 入口函数中增加判断逻辑。

### 报告问题

若发现问题，请提供以下信息：
1. 运行模式（`basic` / `with_images`）
2. 完整的错误日志（位于 `logs/` 目录）
3. Python 版本和操作系统信息
4. ffmpeg 版本（`ffmpeg -version`）

---

> **文档版本**：v1.3
> **更新日期**：2026-05-25
> **基于项目**：bili-video-notes-workflow v1.4.0
