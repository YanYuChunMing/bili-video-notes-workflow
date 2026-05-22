# Implementation Prompt: 学习单元驱动截图 · 中期方案

---

## 1. Role And Mission

你是一个 Python 项目维护型 AI coding agent。你的任务是在当前 B 站视频笔记项目中实现"学习单元驱动截图"中期方案。请遵循以下约束：

- **不要大范围重构**。不改无关功能，不清理无关乱码文案。
- **只围绕 `with_images` 模式的截图与图文稿生成做可验证改造**。
- **保留旧截图策略**（`DefaultScreenshotter`），新增 `LearningScreenshotter` 并存。
- **不改 `basic` 模式行为**。

**最终使命**：用户希望生成的带图文字稿可以替代原视频学习。实现完成后，读者应该能通过图文稿理解视频中的主要讲解顺序、关键操作、代码/界面/结果画面，而不是只能看到若干随机时间点截图。输出物不再是"带截图的字幕流水账"，而是"结构化图文教程"。

**目标结果**：
- 每张图都要服务于一个学习单元，例如概念、步骤、界面、代码、例题或结果。
- 对操作类视频，优先截取"操作入口 + 操作后结果"。
- 对 PPT/代码/软件界面类视频，优先截取清晰、稳定、信息完整的画面。
- 旧的基础模式不受影响，旧截图策略保留兼容。
- 实现过程必须分块推进：**每完成一个完整功能块，立即运行针对该块的测试或最小验证，确认无明显 bug 后再进入下一块。**
- 全过程必须保持命名规范，避免随意缩写、混用中英文拼音变量名、含糊命名和临时性函数名。

---

## 2. Current Project Context

### 2.1 项目入口

主入口在 `main.py`，核心函数是 `process_single_video()`：

```python
# main.py L23-28
def process_single_video(url: str, task_config: dict, config: dict, index: int) -> bool:
    mode = task_config.get("mode", "basic")
    with_images = mode == "with_images"
    screenshot_enabled = config["screenshot"].get("enabled", False) or with_images
```

**关键流程**（`main.py` L39-131）：
1. `download_video()` 或 `download_audio()` 下载，返回 `{title, audio_path, video_path, video_segments}`。
2. Whisper 转录，得到 `segments`（每个 segment 含 `start`, `end`, `text`）。
3. 文本清洗 + 摘要 + 思维导图（basic 和 with_images 都走）。
4. `with_images` 模式的截图逻辑（L85-125）：
   - 遍历 `video_segments` 列表（大视频可能被 `video_splitter.split_video()` 切割为多段）。
   - 每段：用 `video_splitter.filter_and_adjust_segments()` 将原始 segments 偏移调整为分段内时间。
   - 保存调整后的 `segments_part_NNN.json`。
   - `DefaultScreenshotter(config).process(seg_video_path, seg_segments_path, seg_output_dir)` 返回 `{local_timestamp: image_relative_path}`。
   - 将 local timestamp 加上 offset 转为全局时间：`all_screenshots[global_ts] = f"segment_{seg_idx:03d}/{img_path}"`。
5. 所有分段截图汇总后，调用 `markdown_builder.build_transcript_with_images(segments, all_screenshots, results_dir, title)` 生成 `transcript_with_images.md`。

### 2.2 当前截图策略：`src/screenshotter.py`

文件结构：
- `ScreenshotterInterface`：抽象基类，定义了 `process(video_path, segments_path, output_dir) -> dict` 接口。构造函数读取 `config["screenshot"]` 中的 `min_interval_seconds`、`max_avg_per_minute`、`difference_threshold`、`enabled`。
- `DefaultScreenshotter(ScreenshotterInterface)`：当前实现。核心逻辑（L77-171）：
  1. 从 `segments_path` JSON 加载 segments。
  2. `cv2.VideoCapture` 打开视频，获取 fps 和 duration。
  3. `_get_candidate_times()` 从 segments 中取候选时间：segment 时长≥15s 取中点，否则取起点。
  4. 按候选时间逐帧读取，用 `skimage.metrics.structural_similarity`（SSIM）与上一张图比较，相似度 > `difference_threshold`(0.85) 则跳过。
  5. 满足 `min_interval` 和 `max_avg_per_minute` 约束后保存截图。
  6. 返回 `{timestamp_seconds: "images/xxx.jpg"}`。

**当前策略的问题**：
- 它知道"画面有没有变"，但不知道"这张图是否有教学价值"。
- 它不会按学习步骤组织内容。
- 它容易漏掉操作完成后的结果界面。
- 它容易截到转场、模糊、说话中间态或重复界面。

### 2.3 当前图文稿生成：`src/markdown_builder.py`

```python
# markdown_builder.py L9-41
def build_transcript_with_images(segments: list, screenshots: dict, output_dir: str, title: str = "") -> str:
```

逻辑：
1. 逐个 segment 输出 `[HH:MM:SS] segment_text`。
2. 遍历 `screenshots` 字典，如果截图时间戳落在 segment 的 `[start, end]` 范围内，则插入 `![截图 HH:MM:SS](../{img_path})`。
3. 输出到 `results/transcript_with_images.md`。

**问题**：完全是按字幕时间流水插图，没有学习单元结构。

### 2.4 关键工具函数：`src/utils.py`

```python
def load_json(filepath, default=None)           # 读取 JSON
def save_json(filepath, data)                    # 保存 JSON
def seconds_to_timestamp(seconds: float) -> str  # 秒数 → "MM:SS" 或 "HH:MM:SS"
def timestamp_to_filename(seconds: float) -> str # 秒数 → "HH_MM_SS"
def write_text_file(filepath, content)           # 写文本文件
```

### 2.5 视频分段工具：`src/video_splitter.py`

```python
def filter_and_adjust_segments(original_segments, offset, seg_duration) -> list[dict]
    # 将原始 segments 偏移调整为分段内时间，过滤掉不在当前分段范围内的 segment
def split_video(video_path, output_dir, max_duration_minutes=60) -> list[dict]
    # 返回 [{"path": ..., "start_offset": ..., "duration": ..., "index": ...}]
```

### 2.6 配置系统：`src/config_loader.py`

- 使用 `tomllib` 加载 `config.toml`。
- `_deep_merge()` 将用户配置合并到 `DEFAULT_CONFIG` 上。
- 当前 screenshot 默认配置（L28-33）：
  ```python
  "screenshot": {
      "enabled": False,
      "min_interval_seconds": 5,
      "max_avg_per_minute": 5,
      "difference_threshold": 0.85,
  }
  ```

### 2.7 现有配置文件：`config.example.toml`

```toml
[screenshot]
enabled = false
min_interval_seconds = 5
max_avg_per_minute = 5
difference_threshold = 0.85
```

### 2.8 现有文件结构

```
bili_video/
  main.py
  config.example.toml
  src/
    __init__.py
    config_loader.py
    downloader.py
    link_parser.py
    markdown_builder.py
    mindmap.py
    screenshotter.py
    summarizer.py
    text_cleaner.py
    transcriber.py
    utils.py
    video_splitter.py
```

---

## 3. Engineering Rules

### 3.1 分块实现 + 立即测试（最高优先级）

**你必须严格遵守**：每完成一个完整功能块后立刻测试，测试失败必须先修复当前块，不能继续写下一块。不要一次性写完整套功能后才测试。

测试顺序与内容：

| 块 | 完成后立即做什么 |
|----|-----------------|
| 学习单元构建器 | 用 mock segments 测试切分、cue 识别、标题生成 |
| 候选时间生成器 | 测试边界、去重、操作词后移候选 |
| 帧评分器 | 用合成帧或短视频测试清晰度、重复过滤、评分排序 |
| Markdown 构建器 | 用 mock learning_units 测试图片路径和输出结构 |
| 主流程接入 | 跑一次端到端或最小集成验证 |

### 3.2 命名规范

- **Python 文件名**：使用 `snake_case.py`。
- **函数、变量、字段**：使用 `snake_case`。
- **类名**：使用 `PascalCase`。
- **常量**：使用 `UPPER_SNAKE_CASE`。
- **布尔变量**：使用清晰前缀，例如 `is_`、`has_`、`should_`、`enable_`。
- **禁止使用的命名**：`tmp`、`data2`、`foo`、`xxx`、`ss` 这类含糊命名，除非是极小局部临时变量且上下文非常清楚。
- **禁止混用拼音变量名**：新增代码统一使用英文命名。
- **配置项命名**：与现有风格一致，例如 `max_images_per_unit`、`prefer_after_action_seconds`。

### 3.3 改动聚焦

- 不做无关 UI 重写。
- 不删除旧截图策略（`DefaultScreenshotter` 和 `_get_candidate_times` 全部保留）。
- 不改 `basic` 模式行为。
- 不进行全项目格式化。

---

## 4. Target Architecture

### 4.1 新增文件

**`src/learning_units.py`**：学习单元数据结构和构建逻辑。

```python
from dataclasses import dataclass, field

@dataclass
class LearningUnit:
    unit_id: str                # 唯一标识，如 "unit_01"
    title: str                  # 简短标题，如 "步骤：运行代码"、"结果：查看输出"
    start: float                # 时间范围起点（秒，全局坐标系）
    end: float                  # 时间范围终点（秒，全局坐标系）
    text: str                   # 合并后的字幕文本
    unit_type: str              # concept | operation | code | slide | example | result | summary | unknown
    visual_need: str            # none | low | medium | high
    cue_score: float            # cue 词匹配的综合得分（0.0 ~ 1.0）
    candidate_times: list[float] = field(default_factory=list)  # 候选截图时间戳
    selected_images: list[dict] = field(default_factory=list)   # 已选中的截图
```

`selected_images` 中每个元素的字段：
```python
{
    "timestamp": float,     # 截图全局时间戳
    "path": str,            # 相对图片路径
    "reason": str,          # 选中原因，如 "操作完成后结果界面"
    "score": float,         # 帧评分
}
```

`unit_type` 含义：
- `concept`：概念讲解、理论说明
- `operation`：操作步骤（点击、输入、拖拽等）
- `code`：代码相关
- `slide`：PPT/演示文稿页面
- `example`：示例演示
- `result`：操作结果、输出展示
- `summary`：总结/回顾
- `unknown`：无法判定

`visual_need` 含义：
- `none`：纯口播解释，不需要截图
- `low`：可能有一张图即可
- `medium`：需要截图辅助理解
- `high`：强烈需要截图（代码、界面、操作）

### 4.2 扩展截图模块

在 `src/screenshotter.py` 中新增 `LearningScreenshotter` 类：

```python
class LearningScreenshotter(ScreenshotterInterface):
    """
    学习单元驱动截图策略。

    输入：video_path, segments_path (Whisper segments JSON), output_dir
    流程：
    1. build_learning_units(segments) → list[LearningUnit]
    2. generate_candidate_times(units, video_duration) → 填充各 unit.candidate_times
    3. score_and_select_frames(video_path, units) → 填充各 unit.selected_images
    4. save_screenshots(units, output_dir) → 保存图片，返回 {timestamp: path}
    """

    def process(self, video_path: str, segments_path: str, output_dir: str) -> dict:
        ...
```

**保留 `DefaultScreenshotter` 完整不动**。`LearningScreenshotter` 可单独新建文件 `src/learning_screenshotter.py`，也可放在 `screenshotter.py` 的后面追加。推荐独立新建文件 `src/learning_screenshotter.py` 以保持清晰分离。

### 4.3 配置变更

`config.example.toml` 和 `src/config_loader.py` 的 `DEFAULT_CONFIG` 中的 `[screenshot]` 节需要追加新字段：

```toml
[screenshot]
enabled = false
strategy = "learning"             # "learning" 或 "visual_change"
min_interval_seconds = 3          # 从 5 调整为 3
max_avg_per_minute = 6            # 从 5 调整为 6
max_images_per_unit = 2           # 新增：每个学习单元最多截图数
prefer_after_action_seconds = 1.5 # 新增：操作词后偏好偏移秒数
difference_threshold = 0.85       # 保留
```

`DEFAULT_CONFIG` 中对应的 Python dict 更新：
```python
"screenshot": {
    "enabled": False,
    "strategy": "learning",
    "min_interval_seconds": 3,
    "max_avg_per_minute": 6,
    "max_images_per_unit": 2,
    "prefer_after_action_seconds": 1.5,
    "difference_threshold": 0.85,
}
```

### 4.4 架构总览图

```
Whisper segments
       │
       ▼
┌──────────────────────┐
│  learning_units.py   │
│  build_learning_units│  ← 清洗、合并、cue 词切分、分类、标题生成
└────────┬─────────────┘
         │ list[LearningUnit]
         ▼
┌──────────────────────┐
│  candidate_times.py  │  ← 按单元类型生成候选时间、去重
│  (可放在 learning_   │
│   units.py 或独立)   │
└────────┬─────────────┘
         │ 填充 candidate_times
         ▼
┌──────────────────────────┐
│  learning_screenshotter  │  ← 帧采样、多维度评分、SSIM去重、选图
│  .py                     │
│  score_and_select_frames │
└────────┬─────────────────┘
         │ 填充 selected_images + 保存图片文件
         ▼
┌──────────────────────────┐
│  markdown_builder.py     │
│  build_learning_         │  ← 按学习单元组织图文稿
│  transcript_with_images  │
└────────┬─────────────────┘
         │
         ▼
  learning_transcript_with_images.md
  learning_units.json (调试用)
```

---

## 5. Learning Unit Algorithm

### 5.1 输入

`build_learning_units(segments: list[dict]) -> list[LearningUnit]`

`segments` 是 Whisper 转录输出，每个 segment 至少包含 `start`（float，秒）、`end`（float，秒）、`text`（str）。

### 5.2 步骤 1：清洗

1. 跳过 `text` 为空或只有空白的 segment。
2. 跳过 `text` 为纯标点/纯语气词的 segment（如"嗯"、"啊"、"呃"、"那个"）。
3. 删除 segment `text` 前后的重复短语（Whisper 偶尔会生成"好的好的好的"这类重复）。

### 5.3 步骤 2：合并过短 segment

目标学习单元时长默认 **20-90 秒**。过短的相邻 segment（< 10 秒）按语义或停顿合并，直到合并后的 segment 时长 ≥ 20 秒或遇到强 cue 词需要切分。

合并规则：
1. 如果当前 segment 时长 < 10 秒且下一个 segment 开始间隔 < 1.5 秒，则合并。
2. 合并时 `text` 用空格连接，`start` 取第一个 segment 的 `start`，`end` 取最后一个 segment 的 `end`。
3. 合并后如果仍 < 20 秒，继续合并下一个。

### 5.4 步骤 3：强结构 cue 切分

遇到以下 cue 词时，优先在此处切分学习单元（新单元从该 segment 开始）：

**顺序/步骤类**：
- "第一步"、"第二步"、"第三步"
- "首先"、"然后"、"接着"、"接下来"、"最后"、"其次"、"再次"
- 正则模式匹配：`第[一二三四五六七八九十\d]+步`、`步骤[一二三四五六七八九十\d]+`

**过渡/引导类**：
- "现在我们"、"下面我们"、"接下来我们"
- "这里"、"注意"、"重点"、"关键是"
- "总结一下"、"回顾一下"、"小结"

注意：这些词可能在句中自然出现，需要结合 segment 开头位置判断。优先对 segment `text` 的 **前 8 个中文字符** 做 cue 词匹配，前 8 字命中则视为强切分信号。

### 5.5 步骤 4：cue 词分类与 visual_need 判定

对每个学习单元的 `text` 做全量 cue 词扫描：

**操作 cue → `unit_type = "operation"`, `visual_need >= "medium"`**：
```
点击、打开、选择、输入、复制、粘贴、运行、保存、安装、配置、
切换、拖动、上传、下载、双击、右键、拖动、勾选、取消勾选、
填写、搜索、刷新、回车、退出、重启、启动、停止
```

**结果 cue → `unit_type` 可能为 `"result"`, `visual_need >= "high"`**：
```
成功、失败、报错、输出、生成、效果、结果、完成、可以看到、
可以看到效果、如图所示、如下所示、出现了、弹出了、显示
```

**代码/界面 cue → `visual_need = "high"`**：
```
代码、函数、参数、命令、终端、页面、按钮、菜单、设置、窗口、
表格、图表、命令行、编辑器、IDE、配置文件、API、接口、类、
变量、循环、条件、异常、日志、调试
```

**PPT/演示 cue → `unit_type = "slide"`, `visual_need = "high"`**：
```
PPT、幻灯片、这一页、下一页、翻页、演示、图示、如图所示、图表
```

**概念/解释 cue → `unit_type = "concept"` 或保持 `"unknown"`, `visual_need = "low"` 或 `"none"`**：
- 纯口播解释、背景介绍、闲聊、过渡语。
- 判断依据：连续多个 segment 不命中上述任何视觉 cue 词。

**cue_score 计算**：
```python
cue_score = min(1.0, (operation_hits * 0.15 + result_hits * 0.20 + visual_hits * 0.25 + structure_hits * 0.10))
```

**visual_need 最终判定**：
```python
if visual_hits >= 2 or result_hits >= 1:
    visual_need = "high"
elif operation_hits >= 2 or (operation_hits >= 1 and visual_hits >= 1):
    visual_need = "high"
elif operation_hits >= 1 or visual_hits >= 1:
    visual_need = "medium"
elif cue_score > 0.3:
    visual_need = "low"
else:
    visual_need = "none"
```

### 5.6 步骤 5：标题生成

每个学习单元生成简短标题，规则如下：

```python
def generate_unit_title(unit: LearningUnit) -> str:
    # 取 unit.text 的前 12-24 个中文字符作为候选标题
    text_clean = re.sub(r'[^\u4e00-\u9fff\w]', '', unit.text)
    base_title = text_clean[:18] if len(text_clean) > 18 else text_clean

    # 按 unit_type 加前缀
    prefixes = {
        "operation": "操作",
        "code": "代码",
        "slide": "PPT",
        "example": "示例",
        "result": "结果",
        "summary": "总结",
        "concept": "概念",
    }
    prefix = prefixes.get(unit.unit_type, "")
    if prefix and not base_title.startswith(prefix):
        return f"{prefix}：{base_title}"
    return base_title or "未命名"
```

### 5.7 单元 ID 生成

```python
unit_id = f"unit_{idx:03d}"  # idx 从 01 开始递增
```

---

## 6. Candidate Time Algorithm

### 6.1 函数签名

```python
def generate_candidate_times(
    units: list[LearningUnit],
    video_duration: float,
) -> list[LearningUnit]:
    # 直接修改每个 unit 的 candidate_times 字段，返回 units
```

### 6.2 基础候选时间

每个学习单元生成 3 个基础候选时间（全部 `visual_need != "none"` 的单元）：

```python
base_candidates = [
    unit.start + 1.0,           # 单元开始后 1 秒
    (unit.start + unit.end) / 2,  # 单元中点
    unit.end - 1.0,             # 单元结束前 1 秒
]
```

**注意**：如果 `unit.end - 1.0 <= unit.start + 1.0`（单元过短），只取中点 `(unit.start + unit.end) / 2`。

### 6.3 操作类单元额外候选

当 `unit_type == "operation"` 且 text 中包含操作 cue 词时，在操作词对应时间后追加候选：

从 unit 的 segments 中查找操作 cue 词的位置，估算 cue_time（取包含该 cue 词的 segment 的 end）：

```python
extra_operation_candidates = [
    cue_time + 0.8,
    cue_time + 1.5,   # 操作后 1.5 秒——操作完成后的结果界面
    cue_time + 2.5,
]
```

### 6.4 结果类单元额外候选

当 unit 命中结果 cue 时：

```python
extra_result_candidates = [
    result_cue_time + 1.0,
    result_cue_time + 2.0,
    unit.end - 0.5,    # 单元结束前 0.5 秒——最可能的结果展示
]
```

### 6.5 边界约束

```python
def clamp_candidates(candidates: list[float], unit_start: float, unit_end: float, video_duration: float) -> list[float]:
    clamped = []
    for t in candidates:
        # 必须落在 [0, video_duration] 内
        t = max(0.0, min(t, video_duration))
        # 必须落在学习单元时间范围内
        if unit_start <= t <= unit_end:
            clamped.append(round(t, 2))
    return clamped
```

### 6.6 去重

相近候选合并：如果两个候选时间相差 ≤ 0.5 秒，取两者平均值，只保留一个。

```python
def deduplicate_candidates(candidates: list[float], threshold: float = 0.5) -> list[float]:
    if not candidates:
        return []
    sorted_times = sorted(set(candidates))
    result = [sorted_times[0]]
    for t in sorted_times[1:]:
        if t - result[-1] > threshold:
            result.append(t)
        else:
            # 合并：取平均值
            result[-1] = round((result[-1] + t) / 2, 2)
    return result
```

### 6.7 候选为空时的兜底

如果去重后 `candidate_times` 为空，使用学习单元中点作为唯一个候选：

```python
if not unit.candidate_times:
    unit.candidate_times = [(unit.start + unit.end) / 2]
```

### 6.8 visual_need == "none" 的处理

`visual_need == "none"` 的学习单元不生成候选时间。`candidate_times` 保持空列表。

---

## 7. Frame Scoring Algorithm

### 7.1 总体要求

- 使用 **OpenCV（cv2）+ scikit-image**，不引入视觉大模型。
- 从每个候选时间附近采样多帧，选评分最高的一帧作为该候选位置的截图。
- 核心目标：**选教学价值最高的稳定帧，而不是视觉变化最大的帧。**

### 7.2 多帧采样

对每个候选时间 `t`，采样以下时间点的帧：

```python
sample_offsets = [-0.5, 0.0, 0.5, 1.0]
sample_times = [round(t + offset, 2) for offset in sample_offsets]
```

对每个采样时间点读取一帧（使用 `cv2.VideoCapture.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)`），计算评分。

### 7.3 评分维度

#### 7.3.1 清晰度评分 `clarity_score`（权重 0.35）

使用灰度图 Laplacian variance：

```python
def compute_clarity_score(gray_frame: np.ndarray) -> float:
    laplacian = cv2.Laplacian(gray_frame, cv2.CV_64F)
    variance = laplacian.var()
    # 归一化到 [0, 1]，经验参考值：清晰图 > 500，模糊图 < 100
    return min(1.0, variance / 800.0)
```

#### 7.3.2 稳定性评分 `stability_score`（权重 0.25）

与前后采样帧的 SSIM 较高说明不是转场中间态：

```python
def compute_stability_score(gray_frame: np.ndarray, prev_gray: np.ndarray, next_gray: np.ndarray) -> float:
    # 缩放到统一尺寸加速 SSIM 计算
    small = cv2.resize(gray_frame, (160, 90))
    small_prev = cv2.resize(prev_gray, (160, 90))
    small_next = cv2.resize(next_gray, (160, 90))

    ssim_prev = structural_similarity(small, small_prev)
    ssim_next = structural_similarity(small, small_next)
    return (ssim_prev + ssim_next) / 2.0  # 已经是 [0, 1]
```

注意：边界帧（候选时间对应的首帧或末帧）缺少前/后帧时，SSIM 与自身比较得 1.0。

#### 7.3.3 信息量评分 `information_score`（权重 0.20）

边缘密度或灰度变化丰富度，避免纯黑、纯白、空白页：

```python
def compute_information_score(gray_frame: np.ndarray) -> float:
    # Canny 边缘检测
    edges = cv2.Canny(gray_frame, 50, 150)
    edge_density = np.sum(edges > 0) / edges.size
    # 灰度标准差
    gray_std = np.std(gray_frame) / 128.0  # 归一化

    # 综合分数
    return min(1.0, edge_density * 3.0 + gray_std * 0.5)
```

额外惩罚规则：
- 如果灰度均值 < 10（纯黑）或 > 245（纯白）：`information_score` 直接归零。
- 如果灰度方差 < 5（几乎纯色）：`information_score` 减半。

#### 7.3.4 重复惩罚 `duplicate_penalty`（权重 0.30）

与上一张已选中的最佳帧做 SSIM 比较：

```python
def compute_duplicate_penalty(gray_frame: np.ndarray, last_selected_gray: np.ndarray | None) -> float:
    if last_selected_gray is None:
        return 0.0  # 第一张图不罚

    small = cv2.resize(gray_frame, (160, 90))
    small_last = cv2.resize(last_selected_gray, (160, 90))
    ssim_val = structural_similarity(small, small_last)

    # SSIM > 0.90 时开始惩罚，SSIM > 0.98 时惩罚接近 1.0
    if ssim_val < 0.85:
        return 0.0
    return min(1.0, (ssim_val - 0.85) / 0.15)
```

#### 7.3.5 Cue 加成 `cue_bonus`（权重 0.15）

```python
def compute_cue_bonus(sample_time: float, unit: LearningUnit) -> float:
    bonus = 0.0

    # 操作后偏好：如果是"操作 cue"后的时间，且有 1.5 秒偏移
    if unit.unit_type == "operation":
        # sample_time 靠近 unit.start + 1.5 的范围加分
        prefer_time = unit.start + 1.5
        dist = abs(sample_time - prefer_time)
        if dist < 2.0:
            bonus += (2.0 - dist) / 2.0 * 0.6  # 最高加 0.6

    # 结果偏好：如果是"结果 cue"且 sample_time 靠近 unit.end
    if unit.unit_type == "result":
        # 靠近 unit.end 附近加分
        dist = unit.end - sample_time
        if 0 <= dist <= 3.0:
            bonus += (3.0 - dist) / 3.0 * 0.8  # 最高加 0.8

    return min(1.0, bonus)
```

### 7.4 综合评分公式

```python
score = (
    clarity_score * 0.35
    + stability_score * 0.25
    + information_score * 0.20
    + cue_bonus * 0.15
    - duplicate_penalty * 0.30
)
```

### 7.5 选择逻辑

对每个学习单元：

1. 遍历所有 `candidate_times`，对每个候选时间采样 4 帧，计算每帧评分。
2. 取评分最高的一帧作为该候选时间的代表帧。
3. 按评分对所有候选的代表帧降序排序。
4. 从中选取 top N（N = `max_images_per_unit`，默认 2），跳过 `duplicate_penalty > 0.7` 的帧。
5. 将选中的帧信息写入 `unit.selected_images`。
6. 更新 `last_selected_gray` 为当前选中帧，用于后续单元的重复惩罚。
7. 全局 `min_interval` 约束也适用：如果距上一个截图时间 < `min_interval_seconds`，跳过当前帧。

```python
def score_and_select_frames(
    video_path: str,
    units: list[LearningUnit],
    config: dict,
) -> list[LearningUnit]:
    max_per_unit = config["screenshot"]["max_images_per_unit"]
    min_interval = config["screenshot"]["min_interval_seconds"]
    prefer_after = config["screenshot"]["prefer_after_action_seconds"]

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    video_duration = total_frames / fps if fps > 0 else 0

    last_selected_gray = None
    last_selected_time = -min_interval

    for unit in units:
        if not unit.candidate_times:
            continue

        scored_candidates = []
        for t in unit.candidate_times:
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

                clarity = compute_clarity_score(gray)

                # 获取前后帧计算稳定性
                # (简化：用同候选时间的相邻采样帧做比较)
                stability = 0.8  # 默认值，实际需要前后帧

                info_score = compute_information_score(gray)
                dup_penalty = compute_duplicate_penalty(gray, last_selected_gray)
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
                    "frame": frame,
                    "score": score,
                    "reason": f"clarity={clarity:.2f} stability={stability:.2f} info={info_score:.2f} cue={cue_bonus:.2f} dup={dup_penalty:.2f}",
                })

        # 按评分降序排序
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)

        # 选取 top N
        selected = []
        for cand in scored_candidates:
            if len(selected) >= max_per_unit:
                break
            # 跳过评分过低或重复度过高的
            if cand["score"] < 0.1:
                continue
            # 全局 min_interval 约束
            if abs(cand["timestamp"] - last_selected_time) < min_interval:
                continue
            selected.append(cand)
            last_selected_gray = cand["gray"]
            last_selected_time = cand["timestamp"]

        unit.selected_images = [
            {
                "timestamp": s["timestamp"],
                "path": "",  # 待 save 时填充
                "reason": s["reason"],
                "score": round(s["score"], 4),
            }
            for s in selected
        ]

    cap.release()
    return units
```

### 7.6 保存截图

遍历所有 learning units，保存 `selected_images` 中每张图片：

```python
def save_learning_screenshots(
    video_path: str,
    units: list[LearningUnit],
    output_dir: str,
) -> dict:
    images_dir = os.path.join(output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

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

            filename = timestamp_to_filename(ts) + ".jpg"
            filepath = os.path.join(images_dir, filename)
            buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])[1]
            with open(filepath, "wb") as f:
                f.write(buf.tobytes())

            relative_path = os.path.join("images", filename)
            img["path"] = relative_path
            screenshots[ts] = relative_path

    cap.release()
    return screenshots
```

---

## 8. Markdown Output Requirements

### 8.1 新增函数

在 `src/markdown_builder.py` 中新增：

```python
def build_learning_transcript_with_images(
    learning_units: list[LearningUnit],
    output_dir: str,
    title: str = "",
    video_duration: float = 0.0,
) -> str:
```

### 8.2 输出文件

- `results/transcript_with_images.md`：旧的名称保留，用于兼容。
- `results/learning_transcript_with_images.md`：新的学习单元驱动图文稿（新增）。
- `results/learning_units.json`：调试输出，包含完整 `LearningUnit` 数据（新增）。

### 8.3 输出结构

```markdown
# 视频标题

---

## 1. 学习单元标题

> 时间：00:01:20 - 00:02:05  
> 类型：operation | 截图需求：high

![截图 00:01:36](../segment_001/images/00_01_36.jpg)
*截图原因：操作完成后结果界面（score=0.82）*

![截图 00:01:38](../segment_001/images/00_01_38.jpg)
*截图原因：操作入口界面（score=0.75）*

文字内容（Whisper 转录的原始文本）……

---

## 2. 学习单元标题

> 时间：00:02:05 - 00:03:30  
> 类型：code | 截图需求：high

![截图 00:02:30](../segment_001/images/00_02_30.jpg)
*截图原因：完整代码展示（score=0.91）*

文字内容……

---

## 3. 纯口播单元（无图）

> 时间：00:03:30 - 00:04:00  
> 类型：concept | 截图需求：none

文字内容……

---
```

### 8.4 具体要求

1. 图片必须出现在对应学习单元内，不能在错误的时间区域。
2. 每张图下面写一行斜体说明，格式 `*截图原因：{reason}（score={score}）*`。
3. 没有图片的学习单元（`visual_need == "none"` 或没有选出合适的截图）也要保留文字，避免内容断裂。
4. 标题使用序号 `## 1.`、`## 2.` 递增。
5. 使用 `---` 分隔不同学习单元。
6. 时间格式使用 `utils.seconds_to_timestamp()`，即 `HH:MM:SS` 或 `MM:SS`。
7. 图片路径使用相对路径 `../segment_NNN/images/xxx.jpg`（与现有风格一致）。

### 8.5 learning_units.json 输出

```python
def save_learning_units_json(units: list[LearningUnit], output_dir: str) -> str:
    data = []
    for u in units:
        data.append({
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
    filepath = os.path.join(output_dir, "learning_units.json")
    utils.save_json(filepath, data)
    logger.info(f"学习单元数据已保存: {filepath}")
    return filepath
```

---

## 9. Integration Requirements

### 9.1 策略选择

在 `main.py` 的 `process_single_video()` 中，截图部分改为策略分发：

```python
# 在 main.py 截图分支中（L85-125 附近）
strategy = config["screenshot"].get("strategy", "learning")

if strategy == "visual_change":
    ss = screenshotter.DefaultScreenshotter(config)
else:
    # 默认 learning
    from src import learning_screenshotter as ls_module
    ss = ls_module.LearningScreenshotter(config)
```

### 9.2 主流程改造要点

改造 `main.py` L85-125 截图部分：

```python
if screenshot_enabled and video_segments:
    all_screenshots = {}
    all_learning_units = []  # 新增：收集所有学习单元

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

        # 策略分发
        strategy = config["screenshot"].get("strategy", "learning")
        if strategy == "visual_change":
            ss = screenshotter.DefaultScreenshotter(config)
        else:
            # learning 策略
            ss = screenshotter.LearningScreenshotter(config)

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

        # 如果是 learning 策略，还可以收集学习单元用于后续输出
        # (需要在 LearningScreenshotter.process 中附加返回 learning_units)
```

### 9.3 坐标系转换

**重要**：分段视频内的坐标需要通过 offset 转换为全局坐标：

- 分段内时间 → OpenCV 读取帧：使用分段内时间。
- 分段内时间 → 全局时间（图文稿排序和匹配）：`global_time = local_time + offset`。
- Whisper segments 已经是全局坐标，`filter_and_adjust_segments()` 已将其转为分段内坐标。
- 图片路径汇总后使用：`segment_NNN/images/xxx.jpg`。

### 9.4 兼容性要求

1. **保留 `build_transcript_with_images()`**：继续生成旧的 `transcript_with_images.md`，不改签名。
2. **新增 `build_learning_transcript_with_images()`**：生成新的 `learning_transcript_with_images.md`。
3. **LearningScreenshotter.process() 返回签名与 DefaultScreenshotter 一致**：`dict[float, str]`。
4. **也生成 `learning_units.json`** 调试文件。

### 9.5 降级策略

如果学习截图策略失败（异常），必须记录 warning 日志，并降级为旧截图策略或无图稿，**不要导致整个视频处理失败**：

```python
try:
    seg_screenshots = ss.process(seg_video_path, seg_segments_path, seg_output_dir)
except Exception as e:
    logger.warning(f"LearningScreenshotter 失败，降级为 DefaultScreenshotter: {e}")
    ss_fallback = screenshotter.DefaultScreenshotter(config)
    ss_fallback.enabled = True
    seg_screenshots = ss_fallback.process(seg_video_path, seg_segments_path, seg_output_dir)
```

### 9.6 Streamlit 页面

Streamlit 页面无需第一版做复杂 UI。只需确保：
- 现有高级设置仍可运行。
- 如果增加 strategy 选择框（可选），默认值为 `learning`。
- 不做 UI 大改。

---

## 10. Implementation Order

**你必须严格按下表顺序逐项完成。每完成一项，立即运行测试/验证，确认通过后再进入下一项。**

| 步骤 | 任务 | 验证方法 |
|------|------|----------|
| **1** | 阅读 `main.py`、`src/screenshotter.py`、`src/markdown_builder.py`、`src/config_loader.py`、`src/utils.py`，确保理解现有流程 | 能用自己的话描述截图从配置到输出的完整链路 |
| **2** | 新增 `src/learning_units.py`：`LearningUnit` dataclass、cue 词词典常量、`build_learning_units()` 函数、`generate_unit_title()` 函数 | 用 mock segments 测试：合并、切分、cue 识别、标题生成 |
| **3** | 立即测试步骤 2 | 编写 `test_learning_units.py` 或直接在脚本中 mock 验证，确保单元切分合理、类型判定正确、视觉需求判定正确 |
| **4** | 在 `src/learning_units.py`（或独立 `src/candidate_times.py`）中新增候选时间生成逻辑：`generate_candidate_times()` | mock 学习单元测试边界、去重、操作词后移、结果词后移 |
| **5** | 立即测试步骤 4 | 验证候选时间不越界、去重正确、操作/结果类单元有额外候选 |
| **6** | 新增 `src/learning_screenshotter.py`：`LearningScreenshotter` 类，包含帧采样、评分、选择逻辑、保存截图 | 用一段 30 秒短视频验证能输出图片、评分排序合理、重复帧被过滤 |
| **7** | 立即测试步骤 6 | 用合成帧或短视频验证清晰度排序、重复过滤、非空输出 |
| **8** | 在 `src/markdown_builder.py` 中新增 `build_learning_transcript_with_images()` 和 `save_learning_units_json()` | mock learning_units 验证 Markdown 结构 |
| **9** | 立即测试步骤 8 | 覆盖有图单元、无图单元、路径正确、时间戳格式正确 |
| **10** | 接入 `main.py` 的 `with_images` 流程：策略分发、LearningScreenshotter 调用、坐标系转换、降级逻辑 | 代码审查 + 最小集成测试 |
| **11** | 更新 `src/config_loader.py` 的 `DEFAULT_CONFIG` 和 `config.example.toml` | 确认新配置项存在且默认值正确 |
| **12** | 运行最小端到端验证：`python main.py --input links_with_images.txt --mode with_images` | 确认流程跑通：下载→转录→学习单元构建→截图→Markdown 生成 |
| **13** | 确认 `basic` 模式不受影响：`python main.py --input links.txt --mode basic` | basic 模式不下载视频、不执行截图，行为保持不变 |

**关键提醒**：
- 步骤 2、4、6、8 完成后都必须立即测试，不能跳过。
- 测试失败必须先修复当前模块的问题，不要继续写下一模块。
- 如果你在第 N 步发现第 N-2 步的 bug，先完成修复和第 N-2 步的重新测试，再回到第 N 步继续。

---

## 11. Tests And Acceptance Criteria

### 11.1 单元测试 / 最小验证覆盖

你必须确保以下测试点通过：

| # | 测试点 | 验证方式 |
|---|--------|---------|
| 1 | cue 词识别是否正确提高 `visual_need` | mock segment 含"点击运行"，验证 `visual_need >= "medium"` |
| 2 | cue 词识别操作类 | mock segment 含"接下来点击打开设置"，验证 `unit_type == "operation"` |
| 3 | cue 词识别结果类 | mock segment 含"运行成功"，验证 `unit_type == "result"` 或 `visual_need == "high"` |
| 4 | 短 segments 合并 | 3 个 < 10 秒的 segments 合并为一个合理的 learning unit |
| 5 | 强结构 cue 切分 | "第一步…" 开头的 segment 应触发新学习单元切分 |
| 6 | 候选时间不越界 | 所有 `candidate_times` 在 `[0, video_duration]` 内 |
| 7 | 操作 cue 后方候选 | 操作类单元的 `candidate_times` 包含 `cue_time + 1.5` |
| 8 | 重复帧 SSIM 过滤 | 连续相同画面只保留第一张 |
| 9 | Markdown 输出学习单元结构 | 输出文件有 `## 1.`、`## 2.` 标题和 `> 时间：` 元信息块 |
| 10 | 无图单元不丢失文字 | `visual_need == "none"` 的单元也有文字内容 |
| 11 | 图片数量不失控 | 每个学习单元最多 `max_images_per_unit` 张图 |
| 12 | 每个功能块完成后有测试记录 | 日志中能看到该功能块的测试通过信息 |

### 11.2 测试命令模板

每个功能块测试的命令示例：

```bash
# 步骤 2-3：学习单元构建测试
python -c "
import json
from src.learning_units import build_learning_units
segments = [
    {'start': 0.0, 'end': 5.0, 'text': '今天我们来讲一下Python的安装'},
    {'start': 5.0, 'end': 12.0, 'text': '首先打开浏览器'},
    {'start': 12.0, 'end': 18.0, 'text': '在地址栏输入python.org'},
    {'start': 18.0, 'end': 25.0, 'text': '点击Download按钮'},
    {'start': 25.0, 'end': 30.0, 'text': '下载完成后双击安装包'},
    {'start': 30.0, 'end': 38.0, 'text': '点击Next一步步安装'},
    {'start': 38.0, 'end': 45.0, 'text': '安装成功后打开命令行输入python'},
]
units = build_learning_units(segments)
for u in units:
    print(f'{u.unit_id} | {u.unit_type:10s} | visual={u.visual_need:6s} | {u.start:.0f}-{u.end:.0f}s | {u.title}')
"

# 步骤 8-9：Markdown 测试
python -c "
from src.learning_units import LearningUnit
from src.markdown_builder import build_learning_transcript_with_images
units = [
    LearningUnit(unit_id='unit_01', title='操作：下载安装', start=0, end=30,
                 text='今天讲Python安装...', unit_type='operation', visual_need='high',
                 cue_score=0.6, candidate_times=[5.0, 15.0], selected_images=[
                     {'timestamp': 5.0, 'path': 'images/00_00_05.jpg', 'reason': '操作入口', 'score': 0.85}
                 ]),
    LearningUnit(unit_id='unit_02', title='概念：语言介绍', start=30, end=60,
                 text='Python是一种...', unit_type='concept', visual_need='none',
                 cue_score=0.1, candidate_times=[], selected_images=[]),
]
content = build_learning_transcript_with_images(units, 'test_output', '测试标题')
print(content)
"
```

### 11.3 人工验收标准

最终实现完成后，用真实视频验证以下几点：

1. **操作教程类视频**：点击、运行、保存之后的结果界面更容易被截到（不被转场帧替代）。
2. **PPT/代码讲解类视频**：完整稳定的页面优先于转场帧，不会截到 PPT 翻页的半透明中间态。
3. **输出 Markdown 结构**：不再只是按字幕时间戳流水插图，而是有 `## 1. 操作：xxx` 这样的章节标题。
4. **图片数量控制**：不会失控，默认仍保持适合阅读的密度。
5. **命令行运行**：`python main.py --input links_with_images.txt --mode with_images` 可以跑通。
6. **basic 模式**：不下载视频、不执行任何截图，行为保持不变。

### 11.4 失败处理

如果任何人工验收标准不通过：
- 首先检查对应模块的单元测试是否遗漏了边界情况。
- 补充测试用例后修复代码。
- 重新运行端到端验证。
- 直到所有验收标准通过。

---

## Appendix: 依赖项

实现本项目需要以下 Python 包（部分已安装）：

```
opencv-python           # cv2，视频帧读取和图像处理
scikit-image            # SSIM 计算
```

现有项目已依赖的基础库：
```
tomllib (Python 3.11+)  # 配置文件解析
python-dotenv           # 环境变量加载
```

---

## Appendix: Q&A / 常见问题

**Q: 如果 LearningScreenshotter 抛出异常怎么办？**
A: 必须用 try/except 包裹，记录 warning 日志，降级为 DefaultScreenshotter 或无图模式。不允许整个视频处理失败。

**Q: 操作 cue 词的时间如何确定？**
A: 当前方案基于 segment 的时间边界估算。如果 segment `end=15.0` 且文本命中"点击"，则 cue_time 取 segment 的 `end`。虽不够精确，但对截图来说已足够。

**Q: 如何避免候选时间超出视频边界？**
A: 每次生成候选时间后都做 clamp（限制在 `[0, video_duration]`），并且去重后再做一次 clamp。

**Q: 单元测试是否需要正式的测试框架？**
A: 不需要 pytest 或 unittest。用简单的命令行脚本验证即可。但必须输出清晰的 pass/fail 结果。

**Q: LearningScreenshotter.process() 的返回值格式？**
A: 与 `DefaultScreenshotter.process()` 完全一致：`dict[float, str]`，key 为分段内时间戳，value 为 `"images/xxx.jpg"` 格式的相对路径。
