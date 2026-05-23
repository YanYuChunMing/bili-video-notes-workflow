# 创建“学习单元驱动截图中期方案”实施 Prompt 文件

## Summary

在当前项目中新建 `docs/learning_screenshot_strategy/IMPLEMENTATION_PROMPT.md`，写入一份可直接交给廉价 AI coding agent 执行的详细实施 prompt。

这份 prompt 的核心目的要写清楚：**把当前 with_images 模式从“按时间/画面变化截图”升级为“按学习单元选择教学截图”，最终让用户可以不看原视频，仅阅读图文版内容，就基本学会视频中的主要知识、步骤、操作和结果。**

目标结果也要明确写入文件：

- 输出物不再是“带截图的字幕流水账”，而是“结构化图文教程”。
- 每张图都要服务于一个学习单元，例如概念、步骤、界面、代码、例题或结果。
- 对操作类视频，优先截取“操作入口 + 操作后结果”。
- 对 PPT/代码/软件界面类视频，优先截取清晰、稳定、信息完整的画面。
- 旧的基础模式不受影响，旧截图策略保留兼容。
- 实现过程必须分块推进：**每完成一个完整功能块，立即运行针对该块的测试或最小验证，确认无明显 bug 后再进入下一块。**
- 全过程必须保持命名规范，避免随意缩写、混用中英文拼音变量名、含糊命名和临时性函数名。

## File To Create

- 新建目录：`docs/learning_screenshot_strategy/`
- 新建文件：`docs/learning_screenshot_strategy/IMPLEMENTATION_PROMPT.md`
- 文件格式：Markdown
- 文件定位：不是普通说明文，而是“可执行实施 prompt”，开头直接写给接手实现的 AI。

## Prompt Content Structure

`IMPLEMENTATION_PROMPT.md` 要包含以下完整内容。

### 1. Role And Mission

写明接手者身份：

> 你是一个 Python 项目维护型 AI coding agent。你的任务是在当前 B 站视频笔记项目中实现“学习单元驱动截图”中期方案。请不要大范围重构，不要改无关功能，不要清理无关乱码文案，只围绕 with_images 模式的截图与图文稿生成做可验证改造。

写明最终使命：

> 用户希望生成的带图文字稿可以替代原视频学习。实现完成后，读者应该能通过图文稿理解视频中的主要讲解顺序、关键操作、代码/界面/结果画面，而不是只能看到若干随机时间点截图。

### 2. Current Project Context

prompt 中要告诉实现者当前项目事实：

- 入口主要在 `main.py` 的 `process_single_video()`。
- `with_images` 模式会下载完整视频，并在转录后调用 `src/screenshotter.py`。
- 当前 `DefaultScreenshotter` 的逻辑是：
  - 从 Whisper segments 取起点或中点作为候选时间。
  - 用 OpenCV 读取视频帧。
  - 用 SSIM 过滤相似画面。
  - 用 `min_interval_seconds` 和 `max_avg_per_minute` 控制数量。
- 当前 `src/markdown_builder.py` 只是按截图时间是否落在 segment 时间范围内插入图片。
- 当前问题：
  - 它知道“画面有没有变”，但不知道“这张图是否有教学价值”。
  - 它不会按学习步骤组织内容。
  - 它容易漏掉操作完成后的结果界面。
  - 它容易截到转场、模糊、说话中间态或重复界面。

### 3. Engineering Rules

prompt 中必须加入强约束：

- 分块实现，每个完整功能块完成后必须立刻测试：
  - 完成学习单元构建器后，先用 mock segments 测试切分、cue 识别、标题生成。
  - 完成候选时间生成后，先测试边界、去重、操作词后移候选。
  - 完成帧评分后，先用合成帧或短视频测试清晰度、重复过滤、评分排序。
  - 完成 Markdown 构建后，先用 mock learning units 测试图片路径和输出结构。
  - 完成主流程接入后，再跑一次端到端或最小集成验证。
- 测试失败时必须先修复当前块，不能继续写下一块。
- 不要一次性写完整套功能后才测试。
- 命名规范：
  - Python 文件名使用 `snake_case.py`。
  - 函数、变量、字段使用 `snake_case`。
  - 类名使用 `PascalCase`。
  - 常量使用 `UPPER_SNAKE_CASE`。
  - 布尔变量使用清晰前缀，例如 `is_`、`has_`、`should_`、`enable_`。
  - 不使用 `tmp`、`data2`、`foo`、`xxx`、`ss` 这类含糊命名，除非是极小局部临时变量且上下文非常清楚。
  - 不混用拼音变量名，新增代码统一使用英文命名。
  - 配置项命名要与现有风格一致，例如 `max_images_per_unit`、`prefer_after_action_seconds`。
- 保持改动聚焦：
  - 不做无关 UI 重写。
  - 不删除旧截图策略。
  - 不改 basic 模式行为。
  - 不进行全项目格式化。

### 4. Target Architecture

要求实现以下中期架构。

新增“学习单元”概念，建议新建 `src/learning_units.py`，包含：

```python
@dataclass
class LearningUnit:
    unit_id: str
    title: str
    start: float
    end: float
    text: str
    unit_type: str
    visual_need: str
    cue_score: float
    candidate_times: list[float]
    selected_images: list[dict]
```

字段含义写入 prompt：

- `unit_type` 可取：`concept`、`operation`、`code`、`slide`、`example`、`result`、`summary`、`unknown`。
- `visual_need` 可取：`none`、`low`、`medium`、`high`。
- `selected_images` 中每个元素至少包含 `timestamp`、`path`、`reason`、`score`。

新增学习截图策略，建议新建或扩展 `src/screenshotter.py`：

```python
class LearningScreenshotter(ScreenshotterInterface):
    def process(self, video_path: str, segments_path: str, output_dir: str) -> dict:
        ...
```

保留旧的 `DefaultScreenshotter`，不要删除。新增配置：

```toml
[screenshot]
strategy = "learning"       # learning 或 visual_change
min_interval_seconds = 3
max_avg_per_minute = 6
max_images_per_unit = 2
prefer_after_action_seconds = 1.5
```

### 5. Learning Unit Algorithm

prompt 中要详细要求实现规则。

学习单元构建输入：Whisper segments，每个 segment 至少有 `start`、`end`、`text`。

处理步骤：

1. 清洗 segment text，跳过空文本。
2. 将过短 segment 合并，目标单元长度默认 20-90 秒。
3. 遇到强结构 cue 时优先切分，例如：
   - “第一步、第二步、首先、然后、接着、最后、总结”
   - “现在我们、接下来、这里、注意、重点”
4. 遇到强操作 cue 时提高截图需求：
   - “点击、打开、选择、输入、复制、粘贴、运行、保存、安装、配置、切换、拖动、上传、下载”
5. 遇到结果 cue 时提高截图优先级：
   - “成功、失败、报错、输出、生成、效果、结果、完成、可以看到”
6. 遇到代码/界面 cue 时判定为视觉强需求：
   - “代码、函数、参数、命令、终端、页面、按钮、菜单、设置、窗口、表格、图表”
7. 纯口播解释类单元可以 `visual_need = low` 或 `none`。
8. 每个学习单元生成一个简短标题；中期可用规则生成，例如取前 12-24 个中文字符，或按 cue 生成“步骤：运行代码”“结果：查看输出”。

### 6. Candidate Time Algorithm

每个学习单元生成候选截图时间。

基础候选：

```text
unit.start + 1.0
(unit.start + unit.end) / 2
unit.end - 1.0
```

操作类单元额外候选：

```text
cue_time + 0.8
cue_time + 1.5
cue_time + 2.5
```

结果类单元额外候选：

```text
result_cue_time + 1.0
result_cue_time + 2.0
unit.end - 0.5
```

边界要求：

- 候选时间必须落在 `[0, video_duration]`。
- 候选时间必须落在当前分段视频内。
- 去重时允许 0.5 秒内的候选合并。
- 如果候选为空，则使用学习单元中点。

### 7. Frame Scoring Algorithm

prompt 中要要求使用 OpenCV + scikit-image，不引入视觉大模型。

每个候选时间附近采样多帧：

```text
t - 0.5, t, t + 0.5, t + 1.0
```

为每帧计算分数：

- 清晰度：灰度图 Laplacian variance，越高越好。
- 稳定性：与前后采样帧 SSIM 较高说明不是转场中间态。
- 信息量：边缘密度或灰度变化丰富度，避免纯黑、纯白、空白页。
- 重复惩罚：与上一张已选图 SSIM 太高则降分或跳过。
- 操作后偏好：如果来源是操作 cue，则 `cue_time + 1.5` 附近加分。
- 结果态偏好：如果包含结果 cue，则靠近结果 cue 后方的帧加分。

建议评分公式写入 prompt：

```python
score = (
    clarity_score * 0.35
    + stability_score * 0.25
    + information_score * 0.20
    + cue_bonus * 0.15
    - duplicate_penalty * 0.30
)
```

要求实现者可以调整细节，但不要改变核心目标：**选教学价值最高的稳定帧，而不是视觉变化最大的帧。**

### 8. Markdown Output Requirements

要求新增或扩展图文稿生成逻辑。推荐新增：

```python
build_learning_transcript_with_images(
    learning_units: list[LearningUnit],
    output_dir: str,
    title: str = "",
) -> str
```

输出结构必须按学习单元组织：

```markdown
# 视频标题

## 1. 学习单元标题

> 时间：00:01:20 - 00:02:05  
> 类型：operation

![截图 00:01:36](../segment_001/images/00_01_36.jpg)

文字内容……

## 2. 学习单元标题
...
```

要求：

- 图片必须出现在对应学习单元内。
- 每张图下面可以写一句简短说明，例如“截图原因：操作完成后的结果界面”。
- 没有图片的学习单元也要保留文字，避免内容断裂。
- 继续生成 `transcript_with_images.md`，不要让用户找不到旧文件。
- 可额外生成 `learning_units.json` 便于调试和后续长期方案升级。

### 9. Integration Requirements

prompt 中要写清楚集成方式：

- `with_images` 默认使用 `screenshot.strategy = "learning"`。
- 如果配置为 `visual_change`，继续调用旧 `DefaultScreenshotter`。
- `main.py` 中分段视频处理仍然保留。
- 分段视频内截图时间要转换成全局时间：
  - 分段内时间用于 OpenCV 读取帧。
  - 全局时间用于图文稿排序和匹配。
- 图片路径继续兼容当前结构：
  - 分段内返回：`images/xxx.jpg`
  - 汇总后返回：`segment_NNN/images/xxx.jpg`
- 如果学习截图失败，记录 warning，并降级为旧截图策略或无图稿，不要导致整个视频处理失败。
- Streamlit 页面无需第一版做复杂 UI，只需现有高级设置仍可运行；如果增加 strategy 选择框，要默认 `learning`。

### 10. Implementation Order

要求廉价 AI 严格按顺序做：

1. 阅读 `main.py`、`src/screenshotter.py`、`src/markdown_builder.py`、`src/config_loader.py`。
2. 新增学习单元构建逻辑和可测试函数。
3. 立刻测试学习单元构建：mock segments 覆盖合并、切分、cue 识别、标题生成。
4. 新增候选时间生成逻辑。
5. 立刻测试候选时间生成：覆盖边界、去重、操作词后移、结果词后移。
6. 新增帧评分与学习截图策略，先保证能输出图片。
7. 立刻测试帧评分：用合成帧或短视频验证清晰度排序、重复过滤、非空输出。
8. 新增学习单元 Markdown 构建函数。
9. 立刻测试 Markdown 构建：mock learning units 覆盖有图、无图、路径、时间戳。
10. 接入 `main.py` 的 with_images 流程。
11. 更新默认配置和 `config.example.toml`。
12. 运行最小端到端验证，确认 `with_images` 跑通。
13. 确认 `basic` 模式不受影响。

### 11. Tests And Acceptance Criteria

prompt 中要明确测试要求：

单元测试或最小验证应覆盖：

- cue 词识别是否正确提高 `visual_need`。
- 短 segments 是否能合并成合理学习单元。
- 候选时间是否不会越界。
- 操作 cue 后方候选时间是否被生成。
- 重复帧是否被 SSIM 过滤。
- Markdown 是否按学习单元输出图片和文字。
- 每个功能块完成后都有对应测试记录或命令输出。

人工验收标准：

- 软件教程中，点击/运行/保存之后的结果界面更容易被截到。
- PPT/代码讲解中，完整稳定页面优先于转场帧。
- 输出 Markdown 不再只是按字幕时间流水插图。
- 图片数量不会失控，默认仍保持适合阅读。
- `python main.py --input links_with_images.txt --mode with_images` 可以跑通。
- `basic` 模式不下载视频、不执行截图，行为保持不变。

## Assumptions

- 文件使用 Markdown，因为用户已选择 Markdown。
- 实际写入路径固定为 `docs/learning_screenshot_strategy/IMPLEMENTATION_PROMPT.md`。
- 当前回合处于 Plan Mode，因此这里不实际创建文件；退出 Plan Mode 后按本计划执行写入。
- 中期方案不接入视觉大模型，但所有结构要为长期多模态 AI 选图预留扩展空间。
- 廉价 AI 实现能力有限，所以 prompt 要写得像任务书：目标、现状、数据结构、算法、接入顺序、分块测试、命名规范、验收标准全部明确。
