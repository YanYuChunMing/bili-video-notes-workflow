# Changelog

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)（Semantic Versioning）规范。
所有值得注意的变更都会被记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 `MAJOR.MINOR.PATCH` 规则。

---

## [1.4.0] - 2026-05-25

### Added

#### Web 平台正式上线

本版本的核心变更是新增基于 **FastAPI + React 19** 的 Web 图形化操作平台，以及基于 **OpenAPI + openapi-typescript** 的前后端 API 契约层。

##### 后端 Web API (`web/`)

- **`web/main.py`** — FastAPI 应用工厂
  - `create_app()` 工厂函数，返回配置完整的 FastAPI 实例
  - CORS 中间件，允许所有来源（开发/内网部署场景）
  - 自动挂载前端构建产物（`frontend/dist/`）为静态文件，启用 SPA fallback
  - `/api/status` 健康检查端点
  - `_inject_openapi_schemas()` — 将未直接作为 `response_model` 引用的 Pydantic 模型注入 `/openapi.json`，确保 openapi-typescript 能发现所有前端需要的类型
  - `_fix_refs()` — 修复 Pydantic `$defs` 与 OpenAPI `#/components/schemas` 的 `$ref` 路径差异

- **`web/models.py`** — 全部 API 数据模型（Pydantic v2）
  - `TaskMode` / `TaskStatus` 枚举
  - `TaskInfo`（12 字段）、`TaskCreateRequest`
  - `ApiResponse[T]` 泛型统一响应包装（code + message + data）
  - `ConfigUpdateRequest`（12 可选字段）
  - `ConfigDisplay` + 4 个子模型：`ProjectConfig` / `WhisperConfig` / `DeepseekConfig` / `ScreenshotConfig`
  - `ApiKeyStatus` / `VideoMetadata`

- **`web/task_manager.py`** — 内存任务管理器：线程安全的任务 CRUD + 后台 daemon 线程执行 `process_single_video()` + progress_callback 实时状态更新 + 删除时清理产物目录

- **路由模块**：
  - `web/routes/tasks.py` — 任务 CRUD API（POST/GET 创建与分页列表、GET/DELETE 单任务）
  - `web/routes/outputs.py` — 产物文件读取 API（7 端点，统一包裹 ApiResponse JSON）
  - `web/routes/config.py` — 配置管理 API（GET/PUT config + GET check API Key）
  - `web/routes/ws.py` — WebSocket 实时进度推送（2s 轮询 + 变化检测）
  - `web/routes/media.py` — 产物静态文件服务（路径穿越防护 + 403 拦截）

##### 前端 SPA (`frontend/`)

- **技术栈**：React 19 + TypeScript 6 + Vite 8 + Tailwind CSS 4
- **7 个页面**：Dashboard / TaskList / TaskDetail / Note / Mindmap / ImageNotes / Settings
- **404 catch-all 路由**
- **共享模块**：`constants/taskStatus.ts`、`hooks/useAsyncEffect.ts`、service 层（axios 封装）

##### API 契约层

- Pydantic → OpenAPI → openapi-typescript → TypeScript 完整类型生成链路
- `frontend/scripts/generate-types.ts` — 从 OpenAPI schema 自动生成 TS 类型
- `frontend/scripts/dump-openapi.ts` — OpenAPI schema 快照导出
- `frontend/openapi.json` + `frontend/src/types/api.generated.ts` 提交 Git

##### 文档

- `docs/API.md` — 完整 REST API + WebSocket 参考文档（15+ 端点）
- `docs/WEB_ARCHITECTURE.md` — Web 平台架构设计文档
- `PROJECT_FRAMEWORK.md` — 新增第 7 章"Web 平台"、版本历史更新

---

## [1.3.0] - 2026-05-23

### Added

#### 学习单元驱动截图策略（`LearningScreenshotter`）

本版本最重要的更新是引入了全新的**学习单元驱动截图策略**，彻底重构了 `with_images` 模式下的截图逻辑，使输出的带图笔记从"带截图的字幕流水账"升级为"结构化图文教程"。

##### 设计动机

旧版截图策略（`DefaultScreenshotter`）基于 SSIM 画面差异度选帧，只关心"画面有没有变"，不关心"这张图是否有教学价值"。导致：
- 容易截到转场模糊帧、说话中间态、纯色/纯黑空白画面
- 优先截取视觉变化大的时刻而非教学信息最丰富的时刻
- 操作类视频容易漏掉"操作完成后的结果界面"
- 输出按字幕时间流水插图，缺乏学习步骤结构

##### 架构概览

新策略采用五阶段流水线架构：

```
Whisper segments → 学习单元构建 → 候选时间生成 → 帧采样评分 → 截图保存 → 结构化Markdown
```

##### 新增文件

- **`src/learning_units.py`** — 学习单元数据结构与构建逻辑
  - `LearningUnit` 数据类：包含 `unit_id`、`title`、`start/end` 时间边界、`unit_type`（操作/代码/PPT/结果/概念/总结）、`visual_need`（none/low/medium/high）、`cue_score`、`candidate_times`、`selected_images`
  - 五大中文 cue 词词典：操作类（28个）、结果类（15个）、代码/视觉类（25个）、PPT/演示类（9个）、结构/过渡类（19个）
  - `build_learning_units()`：Segments 清洗（过滤语气词/纯标点）→ 短 segment 合并（20-90秒目标）→ 强结构 cue 切分（前8字命中即切）→ cue 词分类与 visual_need 判定 → 标题生成
  - `generate_candidate_times()`：基础候选（首/中/尾三点）+ 操作类额外候选（cue_time+0.8/1.5/2.5s）+ 结果类额外候选（cue_time+1.0/2.0s + unit.end-0.5s）→ 边界 clamp → 去重合并

- **`src/learning_screenshotter.py`** — 学习单元驱动截图器
  - `LearningScreenshotter(ScreenshotterInterface)`：继承自现有抽象基类，接口完全兼容
  - **五维度帧评分系统**（加权综合评分）：
    | 评分维度 | 权重 | 技术实现 | 作用 |
    |---------|------|---------|------|
    | 清晰度评分 | 35% | Laplacian variance 归一化 | 过滤模糊/转场帧 |
    | 稳定性评分 | 25% | 前后帧 SSIM 取均值 | 避免转场中间态 |
    | 信息量评分 | 20% | Canny 边缘密度 + 灰度标准差 | 排除纯黑/纯白/空白页 |
    | Cue 词加成 | 15% | 操作后时间偏好 + 结果结束偏好 | 优先操作结果帧 |
    | 重复惩罚 | -30% | 与已选帧 SSIM 比较 | 过滤相似画面 |
  - 每候选时间采样 4 帧（-0.5/0.0/0.5/1.0s 偏移），取评分最高者作为代表帧
  - 全单元 Top-N 选择，支持 `max_images_per_unit` 限制（默认 2 张/单元）
  - 全局 `min_interval_seconds` 间隔约束
  - 异常时自动降级为 `DefaultScreenshotter`

##### 变更前后对比

| 维度 | 旧策略（v1.0-v1.2） | 新策略（v1.3） |
|------|---------------------|---------------|
| **核心思想** | 视觉变化检测 | 教学价值评估 |
| **选帧依据** | SSIM 差异度 >0.85 则保留 | 五维度综合评分排序 |
| **画面过滤** | 仅 SSIM 去重 | 清晰度+稳定性+信息量+重复惩罚 |
| **截图偏好** | 变化大的帧优先 | 操作结果、稳定清晰帧优先 |
| **输出结构** | 字幕时间流水 + 插图 | 学习单元章节 + 图文说明 |
| **候选策略** | 每 segment 取中点/起点 | 基础三点 + 操作偏差 + 结果偏差 |
| **每单元控制** | 全局频率限制 | 每单元最多 N 张 + 全局间隔 |
| **降级处理** | ❌ 无 | ✅ 异常时自动回退旧策略 |

##### 主流程改造

- **策略分发** (`main.py` L122-166)：根据 `config["screenshot"]["strategy"]` 自动选择截图策略，支持 `"learning"`（默认）和 `"visual_change"`（旧策略）两种模式
- **降级保护**：`LearningScreenshotter` 处理异常时，自动 `try/except` 捕获并回退为 `DefaultScreenshotter`，确保不会导致整个视频处理失败
- **跨分段坐标转换**：分段内时间戳通过 `offset` 转换为全局坐标，截图路径汇总为 `segment_NNN/images/xxx.jpg` 格式
- **学习单元跨分段收集**：从各分段的 `learning_units.json` 收集单元数据，叠加 offset 后合并输出全局图文稿

##### 新增 Markdown 输出

- **`build_learning_transcript_with_images()`** (`src/markdown_builder.py` L45-95)：生成 `learning_transcript_with_images.md`，结构如下：
  - `## N. 学习单元标题` 章节化组织
  - `> 时间：HH:MM:SS - HH:MM:SS` 时间元信息块
  - `> 类型：operation | 截图需求：high` 分类标签
  - 每张截图附 `*截图原因：...（score=0.82）*` 斜体说明
  - 无图单元保留文字内容，确保内容不断裂
  - 结尾统计：`共 N 个学习单元，M 张截图`
- **`save_learning_units_json()`** (`src/markdown_builder.py` L98-119)：生成完整 `learning_units.json` 调试输出，包含所有单元的分类、评分、候选时间和选中图片信息
- **旧 `transcript_with_images.md` 保留不变**，确保向后兼容

#### 配置变更

- `[screenshot]` 节新增字段：
  - `strategy = "learning"` — 截图策略选择（`"learning"` 或 `"visual_change"`）
  - `max_images_per_unit = 2` — 每个学习单元最多截图数量
  - `prefer_after_action_seconds = 1.5` — 操作词后偏好偏移秒数
- `[screenshot]` 节调整字段：
  - `min_interval_seconds`：`5` → `3`
  - `max_avg_per_minute`：`5` → `6`
- `config.example.toml` 同步更新
- `DEFAULT_CONFIG` 同步更新（`src/config_loader.py` L28-36）

#### 设计文档

- `docs/learning_screenshot_strategy/IMPLEMENTATION_PROMPT.md` — 完整技术规格文档（~1150行），涵盖：
  - 分块实现策略与测试要求
  - `LearningUnit` 数据结构定义
  - Cue 词词典与分类算法
  - 候选时间生成算法
  - 帧评分多维度数学公式
  - Markdown 输出格式规范
  - 端到端集成要求与验收标准
  - 13 步分块实现检查表

---

## [1.2.0] - 2026-05-22

### Added

#### Docker 容器化支持（CPU + GPU 双版本）

- **Dockerfile**：一键构建的 CPU 版 Docker 镜像，内置 Python 3.12、ffmpeg、全部依赖
- **Dockerfile.gpu**：基于 `nvidia/cuda:12.6.3-cudnn-runtime-ubuntu24.04` 的 GPU 加速版镜像，whisper 转录速度提升 5~15 倍
- **docker-compose.yml**：双 profile 编排（默认 CPU / `--profile gpu`），自动挂载输入输出目录
- **.dockerignore**：排除无关文件，优化构建效率
- **docker_install.ps1**：Windows 一键 Docker Desktop 安装脚本（winget 优先 + 直链备用）
- **docker_install.sh**：Linux / macOS 一键 Docker 安装脚本，自动识别发行版
- **README.md** 新增完整 Docker 章节：系统工程环境要求、GitHub Releases 下载指引、构建运行、GPU 加速配置、常见问题排查
- **README.md** "我应该看哪里"导航表新增 Docker 行（排第一位推荐）
- **README.md** 项目文件结构图新增 Docker 相关文件

#### 代码质量

- `.gitignore` 新增 Docker 排除规则

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

[1.4.0]: https://github.com/YanYuChunMing/bili-video-notes-workflow/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/YanYuChunMing/bili-video-notes-workflow/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/YanYuChunMing/bili-video-notes-workflow/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/YanYuChunMing/bili-video-notes-workflow/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/YanYuChunMing/bili-video-notes-workflow/releases/tag/v1.0.0
