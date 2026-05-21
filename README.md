# bili-video-notes-workflow

> B站视频自动笔记生成工作流 — 一键将 B站视频转化为结构化学习笔记

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📖 项目概述

`bili-video-notes-workflow` 是一个自动化工作流工具，能够将 **B站（bilibili.com）视频** 一键转化为高质量的结构化学习笔记。通过组合 **Whisper 语音转录** 与 **DeepSeek 大语言模型**，实现从视频到笔记的端到端自动化处理。

### 核心能力

| 功能 | 说明 |
|------|------|
| 🎵 音频转录 | 基于 Whisper（faster-whisper / openai-whisper）的高精度语音转文字，支持 GPU 加速 |
| 📝 标点补全 | 通过 DeepSeek API 为无标点转录文本自动添加标点并分段 |
| 📄 学习笔记 | AI 自动提炼核心知识点，生成结构化 Markdown 笔记 |
| 🧠 思维导图 | 自动生成知识思维导图（Markdown + 可浏览 HTML） |
| 📸 智能截图 | 基于 SSIM 结构相似度的关键帧提取，自动去重 |
| 🖼️ 图文笔记 | 将截图匹配到对应文字段落，生成图文并茂的学习笔记 |
| 🔄 断点续跑 | 自动记录处理进度，中断后可从断点继续 |

---

## 🚀 快速开始

### 环境要求

- **Python** ≥ 3.10
- **ffmpeg / ffprobe**（需添加到系统 PATH）
- **yt-dlp**（命令行工具，需单独安装）
- **NVIDIA GPU（可选）**：如需 GPU 加速转录，需 CUDA 支持

### 5 分钟快速部署

```bash
# 1. 克隆项目
git clone https://github.com/YanYuChunMing/bili-video-notes-workflow.git
cd bili-video-notes-workflow

# 2. 创建虚拟环境
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. 安装 Python 依赖
pip install -r requirements.txt

# 4. 安装外部工具
pip install yt-dlp

# 5. 创建配置文件
copy config.example.toml config.toml

# 6. 配置 API Key
copy .env.example .env
# 编辑 .env 填入: DEEPSEEK_API_KEY=sk-your-key-here

# 7. 添加视频链接
echo https://www.bilibili.com/video/BV1xx411c7mD >> links.txt

# 8. 运行
python main.py --task basic_test
```

### 运行模式

| 模式 | 命令 | 输出产物 |
|------|------|---------|
| **Basic**（推荐入门） | `python main.py --task basic_test` | 文字稿 + 笔记摘要 + 思维导图 |
| **With-Images** | `python main.py --task with_images_test` | 上述所有 + 智能截图 + 图文笔记 |
| **命令行直接运行** | `python main.py --input links.txt --mode basic` | 同上 |

---

## 📂 项目结构

```
bili_video/
├── main.py                 # 主入口，流程编排与 CLI
├── _check.py               # 代码质量检查（pyright + AST）
├── requirements.txt        # Python 依赖清单
├── config.example.toml     # 配置文件模板
├── .env.example            # 环境变量模板
├── links.txt               # Basic 模式链接输入
├── links_with_images.txt   # With-Images 模式链接输入
├── PROJECT_FRAMEWORK.md    # 完整项目框架文档
├── CHANGELOG.md            # 版本更新日志
│
└── src/                    # 核心源码
    ├── config_loader.py    # 多层级配置加载
    ├── link_parser.py      # B站链接解析与提取
    ├── downloader.py       # yt-dlp 媒体下载
    ├── video_splitter.py   # ffmpeg 长视频分段
    ├── transcriber.py      # Whisper 语音转录
    ├── text_cleaner.py     # DeepSeek 标点补全
    ├── summarizer.py       # DeepSeek 摘要生成
    ├── mindmap.py          # DeepSeek 思维导图
    ├── screenshotter.py    # OpenCV+SSIM 智能截图
    ├── markdown_builder.py # 图文笔记构建
    └── utils.py            # 通用工具函数
```

---

## ⚙️ 配置说明

### config.toml

```toml
[whisper]
model = "medium"       # 模型大小: tiny/base/small/medium/large
language = "Chinese"   # 转录语言
device = "cuda"        # cuda 或 cpu

[deepseek]
model = "deepseek-chat"
base_url = "https://api.deepseek.com"
max_chunk_minutes = 12 # 分块处理的每块最大对应时长

[screenshot]
enabled = false        # 是否启用截图
min_interval_seconds = 5
max_avg_per_minute = 5
difference_threshold = 0.85  # SSIM 相似度阈值

[[tasks]]
name = "basic_test"
input_file = "links.txt"
mode = "basic"
```

### .env（API 密钥）

```
DEEPSEEK_API_KEY=sk-your-api-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

> ⚠️ **注意**：未配置 API Key 时，AI 功能（标点补全、摘要、思维导图）将自动跳过，仅保留转录功能。

---

## 📊 技术栈

| 层次 | 技术 | 用途 |
|------|------|------|
| 语言 | Python 3.10+ | 核心开发 |
| 媒体下载 | yt-dlp | B站音视频下载 |
| 媒体处理 | ffmpeg / ffprobe | 音频提取、视频切割 |
| 语音转录 | faster-whisper / openai-whisper | 语音→文字 |
| AI 文本 | DeepSeek API (OpenAI 兼容) | 标点、摘要、导图 |
| 繁简转换 | OpenCC | 繁体→简体 |
| 图像处理 | OpenCV + scikit-image (SSIM) | 关键帧提取去重 |
| 配置管理 | TOML + python-dotenv | 配置与环境变量 |

---

## 📚 完整文档

详细的项目框架文档请参阅 [PROJECT_FRAMEWORK.md](PROJECT_FRAMEWORK.md)，包含：

- 项目架构概述与技术栈详解
- 完整的 CLI / API / 内部函数接口信息
- 11 个模块的功能说明与实现逻辑
- 环境配置、部署步骤、常见问题排查
- 数据结构定义与文件存储格式
- 关键业务流程（含流程图）

---

## ⚠️ 已知限制

| 限制项 | 说明 |
|--------|------|
| **基础模式不下载视频** | `basic` 模式仅下载音频，不下载视频文件 |
| **B站登录态** | 当前未集成 Cookie/登录，需登录的视频可能下载失败 |
| **依赖完整性** | `requirements.txt` 未声明 `yt-dlp`，需手动安装 |
| **外部依赖** | `ffmpeg`/`ffprobe` 需单独安装并添加到系统 PATH |
| **AI 功能可选** | 需配置 DeepSeek API Key 才能使用标点/摘要/导图功能 |

---

## 🔧 开发相关

### 代码质量检查

```bash
python _check.py
```

执行 pyright 静态类型检查 + AST 编译检查。

### 输出目录结构

```
outputs/
└── 001_视频标题/
    ├── audio.wav
    ├── segments.json
    ├── metadata.json
    └── results/
        ├── transcript.txt
        ├── transcript_with_timestamps.md
        ├── transcript_with_punct.txt
        ├── summary.md
        ├── mindmap.md
        ├── mindmap.html
        ├── transcript_with_images.md  # with_images 模式
        └── video_segments_report.md   # 长视频切割报告
```

---

## 📄 License

MIT License
