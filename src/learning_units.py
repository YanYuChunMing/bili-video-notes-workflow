import re
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# ============================================================
# Cue word dictionaries
# ============================================================

OPERATION_CUES = [
    "点击", "打开", "选择", "输入", "复制", "粘贴", "运行", "保存", "安装", "配置",
    "切换", "拖动", "上传", "下载", "双击", "右键", "拖动", "勾选", "取消勾选",
    "填写", "搜索", "刷新", "回车", "退出", "重启", "启动", "停止",
]

RESULT_CUES = [
    "成功", "失败", "报错", "输出", "生成", "效果", "结果", "完成", "可以看到",
    "可以看到效果", "如图所示", "如下所示", "出现了", "弹出了", "显示",
]

CODE_VISUAL_CUES = [
    "代码", "函数", "参数", "命令", "终端", "页面", "按钮", "菜单", "设置", "窗口",
    "表格", "图表", "命令行", "编辑器", "IDE", "配置文件", "API", "接口", "类",
    "变量", "循环", "条件", "异常", "日志", "调试",
]

SLIDE_CUES = [
    "PPT", "幻灯片", "这一页", "下一页", "翻页", "演示", "图示", "如图所示", "图表",
]

STRUCTURE_CUES = [
    "第一步", "第二步", "第三步", "首先", "然后", "接着", "接下来", "最后", "其次",
    "再次",
]

TRANSITION_CUES = [
    "现在我们", "下面我们", "接下来我们", "这里", "注意", "重点", "关键是",
    "总结一下", "回顾一下", "小结",
]

STRUCTURE_CUE_PATTERN = re.compile(
    r"第[一二三四五六七八九十\d]+步|步骤[一二三四五六七八九十\d]+"
)

PURE_FILLER_WORDS = {"嗯", "啊", "呃", "那个", "这个", "哦", "唔", "呀", "吧"}


# ============================================================
# LearningUnit dataclass
# ============================================================

@dataclass
class LearningUnit:
    unit_id: str
    title: str
    start: float
    end: float
    text: str
    unit_type: str = "unknown"
    visual_need: str = "none"
    cue_score: float = 0.0
    candidate_times: list[float] = field(default_factory=list)
    selected_images: list[dict] = field(default_factory=list)


# ============================================================
# Helper: text cleaning
# ============================================================

def _is_pure_filler(text: str) -> bool:
    cleaned = re.sub(r"[^\u4e00-\u9fff]", "", text.strip())
    if not cleaned:
        return True
    remaining = cleaned
    for multi_word in sorted(PURE_FILLER_WORDS, key=len, reverse=True):
        remaining = remaining.replace(multi_word, "")
    if not remaining.strip():
        return True
    for char in remaining:
        if char not in PURE_FILLER_WORDS:
            return False
    return True


def _clean_repeated_phrases(text: str) -> str:
    words = list(text)
    if len(words) < 4:
        return text
    result = [words[0]]
    for i in range(1, len(words)):
        if words[i] != result[-1]:
            result.append(words[i])
        else:
            if i + 1 < len(words) and words[i + 1] != result[-1]:
                result.append(words[i])
    return "".join(result)


# ============================================================
# Cue word detection
# ============================================================

def _count_cue_hits(text: str, cue_list: list[str]) -> int:
    count = 0
    for cue in cue_list:
        count += text.count(cue)
    return count


def _has_structure_cue_at_start(text: str) -> bool:
    chinese_chars = re.findall(r"[\u4e00-\u9fff]", text)
    first_8 = "".join(chinese_chars[:8])
    for cue in STRUCTURE_CUES:
        if first_8.startswith(cue):
            return True
    for cue in TRANSITION_CUES:
        if first_8.startswith(cue):
            return True
    if STRUCTURE_CUE_PATTERN.match(first_8):
        return True
    return False


def _classify_unit(text: str):
    operation_hits = _count_cue_hits(text, OPERATION_CUES)
    result_hits = _count_cue_hits(text, RESULT_CUES)
    visual_hits = _count_cue_hits(text, CODE_VISUAL_CUES)
    slide_hits = _count_cue_hits(text, SLIDE_CUES)
    structure_hits = _count_cue_hits(text, STRUCTURE_CUES + TRANSITION_CUES)

    # unit_type determination
    if operation_hits > 0 and result_hits > 0:
        unit_type = "operation"
    elif result_hits >= 2:
        unit_type = "result"
    elif operation_hits >= 1:
        unit_type = "operation"
    elif visual_hits >= 2:
        unit_type = "code"
    elif slide_hits >= 1:
        unit_type = "slide"
    elif visual_hits >= 1:
        unit_type = "code"
    elif structure_hits >= 1:
        unit_type = "concept"
    else:
        unit_type = "unknown"

    # cue_score
    cue_score = min(1.0, operation_hits * 0.15 + result_hits * 0.20 + visual_hits * 0.25 + structure_hits * 0.10)

    # visual_need
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

    return unit_type, visual_need, cue_score


# ============================================================
# Title generation
# ============================================================

def generate_unit_title(unit: LearningUnit) -> str:
    text_clean = re.sub(r"[^\u4e00-\u9fff\w]", "", unit.text)
    base_title = text_clean[:18] if len(text_clean) > 18 else text_clean

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


# ============================================================
# Segment merging
# ============================================================

def _merge_short_segments(segments: list[dict], min_unit_duration: float = 20.0, short_threshold: float = 10.0, gap_threshold: float = 1.5) -> list[dict]:
    if not segments:
        return []

    merged = []
    current = dict(segments[0])

    for i in range(1, len(segments)):
        nxt = segments[i]
        current_dur = current["end"] - current["start"]
        gap = nxt["start"] - current["end"]

        should_merge = False
        if current_dur < short_threshold and gap < gap_threshold:
            should_merge = True
        elif current_dur < min_unit_duration and gap < gap_threshold:
            should_merge = True

        if should_merge:
            current["end"] = nxt["end"]
            current["text"] = current["text"] + " " + nxt["text"]
        else:
            merged.append(current)
            current = dict(nxt)

    merged.append(current)
    return merged


# ============================================================
# Build learning units
# ============================================================

def build_learning_units(segments: list[dict]) -> list[LearningUnit]:
    if not segments:
        return []

    # ---- Step 1: Clean segments ----
    cleaned = []
    for seg in segments:
        text = seg.get("text", "").strip()
        if not text:
            continue
        if _is_pure_filler(text):
            continue
        text = _clean_repeated_phrases(text)
        cleaned.append({
            "start": seg.get("start", 0.0),
            "end": seg.get("end", 0.0),
            "text": text,
        })

    if not cleaned:
        return []

    # ---- Step 2: Merge short segments ----
    merged = _merge_short_segments(cleaned)

    # ---- Step 3: Strong structure cue split ----
    final_segments = []
    for seg in merged:
        if _has_structure_cue_at_start(seg["text"]) and final_segments:
            final_segments.append(seg)
        else:
            if not final_segments:
                final_segments.append(seg)
            else:
                prev = final_segments[-1]
                prev_dur = prev["end"] - prev["start"]
                gap = seg["start"] - prev["end"]
                if prev_dur < 20.0 and gap < 1.5:
                    prev["end"] = seg["end"]
                    prev["text"] = prev["text"] + " " + seg["text"]
                else:
                    final_segments.append(seg)

    # ---- Step 4: Classify and build LearningUnit ----
    units = []
    for idx, seg in enumerate(final_segments, 1):
        unit_type, visual_need, cue_score = _classify_unit(seg["text"])

        unit = LearningUnit(
            unit_id=f"unit_{idx:03d}",
            title="",
            start=seg["start"],
            end=seg["end"],
            text=seg["text"],
            unit_type=unit_type,
            visual_need=visual_need,
            cue_score=cue_score,
        )
        unit.title = generate_unit_title(unit)
        units.append(unit)

    logger.info(f"学习单元构建完成: {len(units)} 个单元 (原始 segments: {len(segments)})")
    return units


# ============================================================
# Candidate time generation
# ============================================================

def _clamp_candidates(candidates: list[float], unit_start: float, unit_end: float, video_duration: float) -> list[float]:
    clamped = []
    for t in candidates:
        t = max(0.0, min(t, video_duration))
        if unit_start <= t <= unit_end:
            clamped.append(round(t, 2))
    return clamped


def _deduplicate_candidates(candidates: list[float], threshold: float = 0.5) -> list[float]:
    if not candidates:
        return []
    sorted_times = sorted(set(candidates))
    result = [sorted_times[0]]
    for t in sorted_times[1:]:
        if t - result[-1] > threshold:
            result.append(t)
        else:
            result[-1] = round((result[-1] + t) / 2, 2)
    return result


def _find_cue_time(text: str, segments_text: str, segments: list[dict], seg_start_idx: int) -> float | None:
    for i in range(len(segments)):
        if text in segments[i].get("text", ""):
            return segments[i].get("end", 0.0)
    return None


def generate_candidate_times(units: list[LearningUnit], video_duration: float, segments: list[dict] | None = None) -> list[LearningUnit]:
    if segments is None:
        segments = []

    for unit in units:
        if unit.visual_need == "none":
            unit.candidate_times = []
            continue

        # Base candidates
        if unit.end - 1.0 > unit.start + 1.0:
            base_candidates = [
                unit.start + 1.0,
                (unit.start + unit.end) / 2,
                unit.end - 1.0,
            ]
        else:
            base_candidates = [(unit.start + unit.end) / 2]

        candidates = list(base_candidates)

        # Extra candidates for operation units
        if unit.unit_type == "operation":
            for cue in OPERATION_CUES:
                if cue in unit.text:
                    cue_time = unit.end
                    candidates.extend([
                        cue_time + 0.8,
                        cue_time + 1.5,
                        cue_time + 2.5,
                    ])
                    break

        # Extra candidates for result units
        if unit.unit_type == "result":
            result_cue_time = unit.end
            for cue in RESULT_CUES:
                if cue in unit.text:
                    result_cue_time = unit.end
                    break
            candidates.extend([
                result_cue_time + 1.0,
                result_cue_time + 2.0,
                unit.end - 0.5,
            ])

        # Clamp
        candidates = _clamp_candidates(candidates, unit.start, unit.end, video_duration)

        # Deduplicate
        candidates = _deduplicate_candidates(candidates)

        # Fallback
        if not candidates:
            candidates = [round((unit.start + unit.end) / 2, 2)]

        unit.candidate_times = candidates

    return units
