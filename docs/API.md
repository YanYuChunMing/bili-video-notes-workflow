# Bili Video Notes — Web API 参考文档

> 本文档涵盖 Web 平台全部 REST API 端点 + WebSocket 协议，基于 FastAPI `/openapi.json` schema 生成。

---

## 目录

1. [通用约定](#1-通用约定)
2. [REST API 端点](#2-rest-api-端点)
   - 2.1 [健康检查](#21-健康检查)
   - 2.2 [任务管理](#22-任务管理)
   - 2.3 [配置管理](#23-配置管理)
   - 2.4 [产物读取](#24-产物读取)
   - 2.5 [媒体文件](#25-媒体文件)
3. [WebSocket 协议](#3-websocket-协议)
4. [数据类型参考](#4-数据类型参考)
5. [错误码说明](#5-错误码说明)

---

## 1. 通用约定

### 1.1 统一响应格式

所有 REST 端点返回统一的 `ApiResponse<T>` 结构：

```json
{
    "code": 0,
    "message": "success",
    "data": {}
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | `int` | 业务状态码：`0` 成功，`400` 请求错误，`404` 未找到，`500` 服务端错误 |
| `message` | `str` | 人类可读的描述信息，成功时为 `"success"` |
| `data` | `T \| null` | 响应载荷，类型取决于具体端点。错误时可能为 `null` |

### 1.2 Base URL

- 开发环境：`http://localhost:8000`
- 生产环境：由部署配置决定

### 1.3 认证

当前版本无需认证。CORS 允许所有来源（`allow_origins=["*"]`）。

### 1.4 版本

当前 API 版本：`v1`（无显式版本号路径前缀，后续版本将加入 `/api/v2/`）。

---

## 2. REST API 端点

### 2.1 健康检查

#### `GET /api/status`

检查服务是否正常运行。

**请求示例**：
```bash
curl http://localhost:8000/api/status
```

**成功响应** (200)：
```json
{
    "code": 0,
    "message": "success",
    "data": {"status": "ok"}
}
```

---

### 2.2 任务管理

#### `POST /api/tasks` — 创建任务

提交一个或多个视频链接进行处理。

**请求体**：

| 字段 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `urls` | `string[]` | 是 | — | 视频链接列表（B站 / 其他 yt-dlp 支持的平台） |
| `mode` | `TaskMode` | 否 | `"basic"` | 处理模式：`basic` / `with_images` |

**请求示例**：
```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://www.bilibili.com/video/BV1xx411c7mD"], "mode": "basic"}'
```

**成功响应** (200)：
```json
{
    "code": 0,
    "message": "success",
    "data": [
        {
            "task_id": "a1b2c3d4e5f6",
            "url": "https://www.bilibili.com/video/BV1xx411c7mD",
            "title": "",
            "mode": "basic",
            "status": "pending",
            "progress": 0.0,
            "stage_message": "",
            "output_dir": "",
            "error_message": "",
            "created_at": "2026-05-25T10:30:00",
            "completed_at": ""
        }
    ]
}
```

> **注意**：返回的 `data` 是数组，每个 URL 对应一个任务。创建成功后任务立即在后台线程启动，可通过 WebSocket 或轮询 GET 端点跟踪进度。

**错误响应** (200 with code=400)：
```json
{"code": 400, "message": "urls 不能为空", "data": null}
```

---

#### `GET /api/tasks` — 任务列表

获取所有任务，支持分页。

**查询参数**：

| 参数 | 类型 | 必填 | 默认 | 说明 |
|------|------|------|------|------|
| `page` | `int` | 否 | `1` | 页码（从 1 开始） |
| `page_size` | `int` | 否 | `20` | 每页条数 |

**请求示例**：
```bash
curl "http://localhost:8000/api/tasks?page=1&page_size=10"
```

**成功响应** (200)：
```json
{
    "code": 0,
    "message": "success",
    "data": {
        "items": [ /* TaskInfo[] */ ],
        "total": 42,
        "page": 1,
        "page_size": 10
    }
}
```

---

#### `GET /api/tasks/{task_id}` — 任务详情

获取单个任务的完整信息。

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `task_id` | `str` | 任务 ID（12 位 hex，如 `a1b2c3d4e5f6`） |

**请求示例**：
```bash
curl http://localhost:8000/api/tasks/a1b2c3d4e5f6
```

**成功响应** (200)：
```json
{
    "code": 0,
    "message": "success",
    "data": {
        "task_id": "a1b2c3d4e5f6",
        "url": "https://www.bilibili.com/video/BV1xx411c7mD",
        "title": "Python 入门教程",
        "mode": "basic",
        "status": "completed",
        "progress": 1.0,
        "stage_message": "处理完成",
        "output_dir": "/path/to/outputs/001_Python_入门教程",
        "error_message": "",
        "created_at": "2026-05-25T10:30:00",
        "completed_at": "2026-05-25T10:35:00"
    }
}
```

**错误响应** (200 with code=404)：
```json
{"code": 404, "message": "任务不存在", "data": null}
```

---

#### `DELETE /api/tasks/{task_id}` — 删除任务

删除任务及其产物目录。

> **约束**：仅 `completed`、`failed` 状态的任务可删除。运行中的任务返回 400。

**请求示例**：
```bash
curl -X DELETE http://localhost:8000/api/tasks/a1b2c3d4e5f6
```

**成功响应** (200)：
```json
{"code": 0, "message": "已删除", "data": null}
```

**错误响应**：
```json
{"code": 400, "message": "任务正在运行中，无法删除", "data": null}
```
```json
{"code": 404, "message": "任务不存在", "data": null}
```

---

### 2.3 配置管理

#### `GET /api/config` — 获取配置

返回当前 `config.toml` + `.env` 的完整合并配置（API Key 以 `has_api_key` 布尔值脱敏展示）。

**请求示例**：
```bash
curl http://localhost:8000/api/config
```

**成功响应** (200)：
```json
{
    "code": 0,
    "message": "success",
    "data": {
        "project": {
            "name": "bili-video-notes-workflow",
            "output_dir": "outputs",
            "log_dir": "logs",
            "temp_dir": "temp",
            "download_dir": "downloads"
        },
        "whisper": {
            "model": "medium",
            "language": "Chinese",
            "device": "cuda",
            "compute_type": "auto"
        },
        "deepseek": {
            "model": "deepseek-chat",
            "base_url": "https://api.deepseek.com",
            "has_api_key": true,
            "max_chunk_minutes": 12
        },
        "screenshot": {
            "enabled": false,
            "strategy": "learning",
            "min_interval_seconds": 3.0,
            "max_avg_per_minute": 6.0,
            "max_images_per_unit": 2,
            "difference_threshold": 0.85
        }
    }
}
```

---

#### `PUT /api/config` — 更新配置

部分更新 `config.toml` 和 `.env`（API Key）。所有字段可选，只更新传入的字段。

**请求体**（全部可选）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `whisper_model` | `str?` | `tiny` / `base` / `small` / `medium` / `large` |
| `whisper_language` | `str?` | 转录语言，如 `"Chinese"` |
| `whisper_device` | `str?` | `cuda` / `cpu` |
| `whisper_compute_type` | `str?` | `float16` / `int8` / `auto` |
| `deepseek_model` | `str?` | 模型名称 |
| `deepseek_base_url` | `str?` | API 基础 URL |
| `deepseek_api_key` | `str?` | API 密钥（写入 `.env`） |
| `screenshot_enabled` | `bool?` | 是否启用截图 |
| `screenshot_strategy` | `str?` | `learning` / `visual_change` |
| `screenshot_min_interval_seconds` | `float?` | 最小截图间隔 |
| `screenshot_max_avg_per_minute` | `float?` | 每分钟最大截图数 |
| `screenshot_difference_threshold` | `float?` | SSIM 相似度阈值 |

**请求示例**：
```bash
curl -X PUT http://localhost:8000/api/config \
  -H "Content-Type: application/json" \
  -d '{"whisper_model": "large", "deepseek_api_key": "sk-xxx"}'
```

**成功响应** (200)：
```json
{"code": 0, "message": "配置已更新", "data": null}
```

**错误响应** (200 with code=500)：
```json
{"code": 500, "message": "config.toml 不存在", "data": null}
```

---

#### `GET /api/config/check` — 检查 API Key

向 DeepSeek API 发送 ping 请求验证 Key 是否有效。

**请求示例**：
```bash
curl http://localhost:8000/api/config/check
```

**成功响应** (200)：
```json
{
    "code": 0,
    "message": "success",
    "data": {
        "valid": true,
        "message": "deepseek-chat"
    }
}
```

**Key 无效 / 网络错误** (200 with code=400)：
```json
{
    "code": 400,
    "message": "success",
    "data": {
        "valid": false,
        "message": "Error code: 401 - Invalid API Key"
    }
}
```

**未配置 Key** (200 with code=400)：
```json
{
    "code": 400,
    "message": "未配置 API Key",
    "data": null
}
```

---

### 2.4 产物读取

所有产物端点均需要任务已 `completed` 且产物文件存在。

#### `GET /api/outputs/{task_id}/summary`

获取 AI 学习笔记摘要（`results/summary.md`）。

**响应**：`ApiResponse<string>` — Markdown 原文。

---

#### `GET /api/outputs/{task_id}/mindmap`

获取思维导图 Markdown 源文件（`results/mindmap.md`）。

**响应**：`ApiResponse<string>` — Markdown 原文。

---

#### `GET /api/outputs/{task_id}/mindmap.html`

获取思维导图 HTML 可视化文件（`results/mindmap.html`）。

**响应**：`ApiResponse<string>` — HTML 原文（可直接 `<iframe>` 渲染）。

---

#### `GET /api/outputs/{task_id}/transcript`

获取纯文字稿（`results/transcript.txt`）。

**响应**：`ApiResponse<string>` — 纯文本。

---

#### `GET /api/outputs/{task_id}/transcript-punct`

获取 AI 标点补全后的文本（`results/transcript_with_punct.txt`）。

**响应**：`ApiResponse<string>` — 纯文本。

---

#### `GET /api/outputs/{task_id}/transcript-images`

获取图文笔记（`results/transcript_with_images.md`）。

> **注意**：仅 `with_images` 模式任务有此文件。

**响应**：`ApiResponse<string>` — Markdown 原文，其中图片引用为相对路径，需配合 `/media` 端点获取实际图片。

---

#### `GET /api/outputs/{task_id}/metadata`

获取视频元数据（`metadata.json`）。

**响应**：`ApiResponse<VideoMetadata>`。

```json
{
    "code": 0,
    "message": "success",
    "data": {
        "title": "Python 入门教程",
        "duration": 1200.5,
        "uploader": "UP主名称",
        "upload_date": "20250101",
        "description": "视频简介文本",
        "webpage_url": "https://www.bilibili.com/video/BV1xx411c7mD"
    }
}
```

**产物端点通用错误**：

| 场景 | 响应 |
|------|------|
| 任务不存在 | `{"code": 404, "message": "任务不存在"}` (HTTP 404) |
| 产物目录不存在 | `{"code": 404, "message": "产物目录不存在"}` (HTTP 404) |
| 特定文件不存在 | `{"code": 404, "message": "文件不存在"}` (HTTP 404) |

---

### 2.5 媒体文件

#### `GET /media/{task_id}/{filepath}`

提供截图等静态文件的访问，用于 Markdown 中图片引用的解析。

**路径参数**：

| 参数 | 类型 | 说明 |
|------|------|------|
| `task_id` | `str` | 任务 ID |
| `filepath` | `str` | 文件在产物目录下的相对路径，如 `segment_000/images/00_00_15.jpg` |

**安全约束**：
- 仅可访问任务 `output_dir` 内的文件
- 路径规范化后若不在 `output_dir` 内 → 403 Forbidden
- 目录遍历攻击防护（`os.path.normpath` 检查）

**请求示例**：
```bash
curl http://localhost:8000/media/a1b2c3d4e5f6/segment_000/images/00_00_15.jpg
```

**响应**：`FileResponse` — 原始图片二进制流（`image/jpeg`）。

**错误响应** (HTTP 404)：
```json
{"detail": "任务不存在"}
{"detail": "产物目录不存在"}
{"detail": "文件不存在"}
```

**错误响应** (HTTP 403)：
```json
{"detail": "禁止访问"}
```

---

## 3. WebSocket 协议

### `WS /ws/tasks/{task_id}`

为单个任务建立实时进度推送连接。前端连接后以 2 秒间隔接收进度更新。

### 消息类型

所有消息均为 JSON 格式：

#### 3.1 `progress` — 进度更新

```json
{
    "type": "progress",
    "task_id": "a1b2c3d4e5f6",
    "stage": "transcribing",
    "message": "正在转录...",
    "progress": 0.35,
    "timestamp": "2026-05-25T10:32:00.123456"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `type` | `str` | 固定为 `"progress"` |
| `task_id` | `str` | 任务 ID |
| `stage` | `str` | 当前阶段，对应 `TaskStatus` 枚举值 |
| `message` | `str` | 人类可读的阶段描述 |
| `progress` | `float` | 当前阶段进度 0.0 ~ 1.0 |
| `timestamp` | `str` | ISO 8601 时间戳 |

**stage 枚举值**：`pending` → `downloading` → `transcribing` → `cleaning` → `summarizing` → `mindmap` → `screenshot` → `completed`

#### 3.2 `complete` — 任务完成

```json
{
    "type": "complete",
    "task_id": "a1b2c3d4e5f6",
    "status": "completed",
    "message": "处理完成",
    "progress": 1.0,
    "timestamp": "2026-05-25T10:35:00.123456"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `type` | `str` | 固定为 `"complete"` |
| `status` | `str` | 终态：`"completed"` 或 `"failed"` |

#### 3.3 `error` — 错误

```json
{
    "type": "error",
    "task_id": "a1b2c3d4e5f6",
    "message": "任务已删除",
    "timestamp": "2026-05-25T10:33:00.123456"
}
```

仅发送于：连接建立后任务被删除的场景。

### WebSocket 生命周期

```
Client                              Server
  │                                   │
  │──── WS /ws/tasks/{task_id} ──────►│ 连接建立
  │◄──── 当前状态 (snapshot) ─────────│ 立即发送
  │                                   │
  │◄──── progress ────────────────────│ 每 2 秒推送
  │◄──── progress ────────────────────│
  │◄──── complete ────────────────────│ 任务结束
  │                                   │
  │──── 断开 ────────────────────────►│ 或客户端主动关闭
```

> **注意**：同 `task_id` 支持多个 WebSocket 连接（`_active_connections[task_id]` 是列表），所有连接均会收到消息推送。

---

## 4. 数据类型参考

### 4.1 枚举

#### `TaskMode`
| 值 | 说明 |
|------|------|
| `"basic"` | 基础模式：仅下载音频 + 转录 + AI 笔记 |
| `"with_images"` | 图文模式：下载视频 + 截图 + 图文笔记 |

#### `TaskStatus`
| 值 | 说明 |
|------|------|
| `"pending"` | 等待处理 |
| `"downloading"` | 正在下载 |
| `"transcribing"` | 语音转录中 |
| `"cleaning"` | 文字清洗中 |
| `"summarizing"` | 生成摘要中 |
| `"mindmap"` | 生成思维导图中 |
| `"screenshot"` | 智能截图中 |
| `"completed"` | 已完成 |
| `"failed"` | 处理失败 |

### 4.2 模型

#### `TaskInfo` — 任务信息
| 字段 | 类型 | 说明 |
|------|------|------|
| `task_id` | `str` | 任务 ID（12 位 hex） |
| `url` | `str` | 视频原始 URL |
| `title` | `str` | 视频标题（完成后填充） |
| `mode` | `TaskMode` | 处理模式 |
| `status` | `TaskStatus` | 当前状态 |
| `progress` | `float` | 进度 0.0 ~ 1.0 |
| `stage_message` | `str` | 当前阶段描述 |
| `output_dir` | `str` | 产物目录路径（完成后填充） |
| `error_message` | `str` | 错误信息（失败时填充） |
| `created_at` | `str` | 创建时间 (ISO 8601) |
| `completed_at` | `str` | 完成时间 (ISO 8601) |

#### `TaskCreateRequest` — 创建任务请求
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `urls` | `string[]` | 是 | 视频链接列表 |
| `mode` | `TaskMode` | 否 | 处理模式，默认 `"basic"` |

#### `ConfigUpdateRequest` — 配置更新请求
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `whisper_model` | `str?` | 否 | Whisper 模型 |
| `whisper_language` | `str?` | 否 | 转录语言 |
| `whisper_device` | `str?` | 否 | 运行设备 |
| `whisper_compute_type` | `str?` | 否 | 计算精度 |
| `deepseek_model` | `str?` | 否 | AI 模型 |
| `deepseek_base_url` | `str?` | 否 | API 地址 |
| `deepseek_api_key` | `str?` | 否 | API Key |
| `screenshot_enabled` | `bool?` | 否 | 启用截图 |
| `screenshot_strategy` | `str?` | 否 | 截图策略 |
| `screenshot_min_interval_seconds` | `float?` | 否 | 最小截图间隔 |
| `screenshot_max_avg_per_minute` | `float?` | 否 | 最大截图频率 |
| `screenshot_difference_threshold` | `float?` | 否 | SSIM 阈值 |

#### `ConfigDisplay` — 完整配置
| 字段 | 类型 | 说明 |
|------|------|------|
| `project` | `ProjectConfig` | 项目路径配置 |
| `whisper` | `WhisperConfig` | Whisper 转录配置 |
| `deepseek` | `DeepseekConfig` | DeepSeek API 配置 |
| `screenshot` | `ScreenshotConfig` | 截图配置 |

#### `VideoMetadata` — 视频元数据
| 字段 | 类型 | 说明 |
|------|------|------|
| `title` | `str` | 视频标题 |
| `duration` | `float` | 总时长（秒） |
| `uploader` | `str` | UP 主名称 |
| `upload_date` | `str` | 上传日期 |
| `description` | `str` | 视频简介 |
| `webpage_url` | `str` | 原始页面 URL |

#### `ApiKeyStatus` — API Key 状态
| 字段 | 类型 | 说明 |
|------|------|------|
| `valid` | `bool` | 是否有效 |
| `message` | `str` | 描述信息（有效时显示模型名，无效时显示错误原因） |

---

## 5. 错误码说明

| HTTP 状态码 | `code` | 触发场景 |
|-------------|--------|---------|
| `200` | `0` | 正常成功 |
| `200` | `400` | 业务参数错误（urls 为空、任务运行中无法删除、API Key 无效等） |
| `200` | `404` | 任务不存在 |
| `200` | `500` | 服务端内部错误（config.toml 缺失、删除失败等） |
| `404` | — | 产物端点：任务/目录/文件不存在（HTTP 原生 404） |
| `403` | — | 媒体端点：路径穿越攻击被拦截（HTTP 原生 403） |

> **设计选择**：错误响应同时存在于 HTTP 200 + `code` 字段 与 HTTP 404/403 两种形式。任务/配置端点使用前者（保持响应格式统一），产物/媒体端点使用后者（FastAPI HTTPException 原生机制）。在实际前端消费中，两种都应处理。

---

> **文档版本**：v1.0
> **更新日期**：2026-05-25
> **基于项目版本**：v1.4.0
