# Bili Video Notes — Web 平台架构文档

> 本文档描述 Web 平台的整体架构设计，包括前后端分层、API 契约、组件树、数据流和部署拓扑。

---

## 目录

1. [架构总览](#1-架构总览)
2. [后端架构](#2-后端架构)
   - 2.1 目录结构
   - 2.2 路由分组
   - 2.3 任务管理模型
   - 2.4 OpenAPI 契约层
3. [前端架构](#3-前端架构)
   - 3.1 技术栈
   - 3.2 目录结构
   - 3.3 路由设计
   - 3.4 组件树
   - 3.5 数据流
4. [API 契约层](#4-api-契约层)
   - 4.1 设计目标
   - 4.2 类型生成链路
   - 4.3 维护流程
5. [WebSocket 实时推送](#5-websocket-实时推送)
6. [静态文件服务](#6-静态文件服务)
7. [部署架构](#7-部署架构)
8. [开发工作流](#8-开发工作流)

---

## 1. 架构总览

```
┌─────────────────────────────────────────────────────────┐
│                      浏览器 (Browser)                     │
│  ┌───────────────────────────────────────────────────┐  │
│  │              React 19 SPA (Vite 8)                │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │  │
│  │  │  Pages   │ │ Services │ │  api.generated.ts │  │  │
│  │  │ (7 页面) │ │ (axios)  │ │ (OpenAPI types)  │  │  │
│  │  └──────────┘ └────┬─────┘ └────────▲─────────┘  │  │
│  └─────────────────────┼───────────────┼─────────────┘  │
└────────────────────────┼───────────────┼────────────────┘
                         │  HTTP + WS   │
                         │  localhost:8000
                         ▼               │
┌────────────────────────┼───────────────┼────────────────┐
│              FastAPI 后端 (Python 3.10+)                 │
│  ┌─────────────────────┼───────────────┼──────────────┐ │
│  │  /api/tasks  /api/outputs  /api/config  /ws/tasks  │ │
│  │  /media                                           │ │
│  └──────────┬─────────────────────────────────────────┘ │
│             │                                            │
│  ┌──────────▼──────────────────────────────────────────┐│
│  │            task_manager (内存任务队列)               ││
│  │   create_task → 后台线程 → progress_callback         ││
│  └──────────┬──────────────────────────────────────────┘│
│             │                                            │
│  ┌──────────▼──────────────────────────────────────────┐│
│  │              main.py process_single_video()          ││
│  │   downloader → transcriber → text_cleaner →         ││
│  │   summarizer → mindmap → screenshotter              ││
│  └─────────────────────────────────────────────────────┘│
│                                                          │
│  ┌──────────────────────────────────────────────────────┐│
│  │          config.toml + .env (配置文件)               ││
│  │          outputs/ (产物目录)                         ││
│  └──────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────┘
```

**核心设计原则**：
- 后端 Pydantic 模型是唯一真相源（Single Source of Truth）
- 前端 TypeScript 类型由 OpenAPI schema 自动生成
- 任务在后台线程执行，WebSocket 推送进度
- 生产构建的前端静态文件由 FastAPI 直接托管（SPA fallback）

---

## 2. 后端架构

### 2.1 目录结构

```
web/                              # Web 平台后端 (FastAPI)
├── __init__.py
├── main.py                       # FastAPI app 工厂、CORS、static mount
├── models.py                     # 全部 Pydantic 模型（API 类型定义）
├── task_manager.py               # 内存任务管理（CRUD + 线程调度）
└── routes/
    ├── tasks.py                  # /api/tasks — 任务 CRUD
    ├── outputs.py                # /api/outputs — 产物文件读取
    ├── config.py                 # /api/config — 配置读写
    ├── ws.py                     # /ws/tasks/{task_id} — WebSocket 进度推送
    └── media.py                  # /media/{task_id}/{filepath} — 静态文件
```

### 2.2 路由分组

| 路由前缀 | 模块 | 端点 | 功能 |
|----------|------|------|------|
| `/api/tasks` | `tasks.py` | `POST/GET/GET{id}/DELETE{id}` | 任务 CRUD |
| `/api/outputs` | `outputs.py` | `GET{id}/summary` 等 7 个 | 产物文件读取 |
| `/api/config` | `config.py` | `GET/PUT` + `GET/check` | 配置管理 + API Key 验证 |
| `/ws/tasks/{id}` | `ws.py` | `WebSocket` | 实时进度推送 |
| `/media/{id}/{path}` | `media.py` | `GET` | 截图等静态文件 |
| `/api/status` | `main.py` | `GET` | 健康检查 |

### 2.3 任务管理模型

```
task_manager.py 职责：
  ┌──────────────────────────────────────┐
  │  _tasks: dict[str, TaskInfo]        │  ← 内存存储（服务重启即清空）
  │  _lock: threading.Lock              │  ← 线程安全
  │                                      │
  │  create_task(url, mode) → TaskInfo   │  创建任务记录
  │  start_task(...) → Thread           │  启动后台处理线程
  │  run_task(...)                      │  后台执行 process_single_video()
  │  progress_callback(stage, msg, %)   │  更新 TaskInfo 状态
  │  get_task / get_all_tasks           │  查询
  │  update_task(task_id, **kwargs)     │  状态更新
  │  delete_task(task_id)              │  删除任务 + 产物目录
  └──────────────────────────────────────┘
```

**任务生命周期**：

```
POST /api/tasks 创建
    │
    ▼
pending ──► downloading ──► transcribing ──► cleaning
                                                 │
                    ┌────────────────────────────┘
                    ▼
              summarizing ──► mindmap ──► screenshot
                    │                            │
                    ▼                            ▼
               completed  ◄────────────────── completed

failed ◄── 任意阶段异常 (exception handler)
```

**设计约束**：
- 任务状态为内存存储，服务重启后历史记录丢失（`processed.json` / `failed.json` 仍在磁盘，但不会自动加载到内存）
- 每个任务在独立 daemon 线程中运行，不阻塞 API 请求
- 运行中的任务（非 completed/failed）禁止删除

### 2.4 OpenAPI 契约层

详见 [4. API 契约层](#4-api-契约层)。后端通过 `_inject_openapi_schemas()` 在应用启动时将未直接作为 `response_model` 的模型注入 `/openapi.json` schema，确保前端能发现所有类型。

**注入的模型**（8 个）：

| 模型 | 注入原因 |
|------|---------|
| `TaskInfo` | 返回时包裹在 `ApiResponse` 泛型内 |
| `TaskStatus` | `str, Enum`，非 BaseModel |
| `ConfigDisplay` | 嵌套组合模型 |
| `WhisperConfig` | 嵌套在 ConfigDisplay 内 |
| `DeepseekConfig` | 嵌套在 ConfigDisplay 内 |
| `ScreenshotConfig` | 嵌套在 ConfigDisplay 内 |
| `ProjectConfig` | 嵌套在 ConfigDisplay 内 |
| `ApiKeyStatus` | check 端点返回泛型包裹 |
| `VideoMetadata` | metadata 端点返回泛型包裹 |

---

## 3. 前端架构

### 3.1 技术栈

| 层 | 技术 | 版本 |
|-----|------|------|
| 框架 | React | 19.x |
| 构建 | Vite | 8.x |
| 语言 | TypeScript | ~6.0.2 |
| 路由 | react-router-dom | 7.x |
| HTTP | axios | 1.x |
| CSS | Tailwind CSS | 4.x |
| 类型生成 | openapi-typescript | 7.x |
| Markdown | react-markdown + remark-gfm | — |
| toast | react-hot-toast | — |

### 3.2 目录结构

```
frontend/
├── package.json
├── tsconfig.json / tsconfig.app.json / tsconfig.node.json
├── vite.config.ts
├── index.html
├── openapi.json                  # OpenAPI schema 快照（提交 Git）
├── scripts/
│   ├── generate-types.ts         # 从后端 /openapi.json 生成 TS 类型
│   └── dump-openapi.ts           # 保存 /openapi.json 快照到本地
└── src/
    ├── main.tsx                  # React 入口
    ├── App.tsx                   # 路由定义（react-router v7）
    ├── App.css                   # 全局样式
    ├── index.css                 # Tailwind 入口
    ├── services/
    │   ├── api.ts                # axios 实例 (baseURL, interceptors)
    │   ├── taskService.ts        # 任务 API 封装
    │   ├── configService.ts      # 配置 API 封装
    │   └── outputService.ts      # 产物 API 封装
    ├── types/
    │   ├── api.generated.ts      # 自动生成（openapi-typescript 输出）
    │   └── api.ts                # 再导出层（人类可读的类型别名）
    ├── hooks/
    │   └── useAsyncEffect.ts     # 复用 Hook：支持取消的异步副作用
    ├── constants/
    │   └── taskStatus.ts         # 状态配置（标签/颜色/图标）
    └── pages/
        ├── DashboardPage.tsx     # 首页：提交新任务
        ├── TaskListPage.tsx      # 任务历史列表
        ├── TaskDetailPage.tsx    # 任务详情 + 进度
        ├── NotePage.tsx          # 学习笔记查看（summary.md）
        ├── MindmapPage.tsx       # 思维导图查看（mindmap.html iframe）
        ├── ImageNotesPage.tsx    # 图文笔记查看
        └── SettingsPage.tsx      # 配置管理页面
```

### 3.3 路由设计

| 路径 | 页面组件 | 说明 |
|------|---------|------|
| `/` | `DashboardPage` | 首页仪表盘，提交新任务 |
| `/tasks` | `TaskListPage` | 任务历史记录 |
| `/tasks/:taskId` | `TaskDetailPage` | 任务详情与实时进度 |
| `/notes/:taskId` | `NotePage` | 学习笔记（summary.md 渲染） |
| `/notes/:taskId/mindmap` | `MindmapPage` | 思维导图（HTML iframe） |
| `/notes/:taskId/images` | `ImageNotesPage` | 图文笔记 |
| `/settings` | `SettingsPage` | 配置管理 |
| `*` | 404 提示 | 未匹配路由（catch-all） |

### 3.4 组件树

```
App (BrowserRouter)
├── Layout (隐式 — 全局 Toast + 导航)
│   ├── <Toaster />                             ← react-hot-toast
│   └── <Routes>
│       ├── "/" → DashboardPage
│       │   ├── 链接输入区 (textarea)
│       │   ├── 模式选择 (basic / with_images)
│       │   └── 提交按钮 → createTask() → 跳转
│       │
│       ├── "/tasks" → TaskListPage
│       │   ├── 任务卡片列表 (status/mode 标签)
│       │   └── 分页
│       │
│       ├── "/tasks/:taskId" → TaskDetailPage
│       │   ├── 进度条 (WebSocket 实时更新)
│       │   ├── 状态/模式/时间信息卡片
│       │   └── 产物入口链接 (summary/mindmap/images)
│       │
│       ├── "/notes/:taskId" → NotePage
│       │   ├── 工具栏 (切换 summary/mindmap/images)
│       │   └── ReactMarkdown 渲染区
│       │
│       ├── "/notes/:taskId/mindmap" → MindmapPage
│       │   └── <iframe> 嵌入 mindmap.html
│       │
│       ├── "/notes/:taskId/images" → ImageNotesPage
│       │   └── ReactMarkdown + 图片懒加载
│       │
│       ├── "/settings" → SettingsPage
│       │   ├── Whisper 配置表单
│       │   ├── DeepSeek 配置 + API Key 测试
│       │   └── Screenshot 配置表单
│       │
│       └── "*" → 404 提示
```

### 3.5 数据流

```
用户操作 ──► Page 组件 ──► Service 函数 ──► axios ──► FastAPI ──► ...
                                                           │
                                     WebSocket ◄───────────┘
                                        │
                                        ▼
                              Page 组件 (useState 更新)
```

**三层数据访问**：

| 层 | 文件 | 职责 |
|-----|------|------|
| HTTP 客户端 | `services/api.ts` | axios 实例，baseURL 配置，通用拦截器 |
| Service 层 | `*Service.ts` | 每个 API 域的函数封装，类型标注 |
| Page 层 | `*Page.tsx` | UI 渲染，调用 service 函数，管理 loading/error 状态 |

**类型安全保障**：

```
backend: models.py (Pydantic)
    │
    ▼  (FastAPI 自动生成)
/openapi.json (OpenAPI 3.1)
    │
    ▼  (openapi-typescript)
frontend/src/types/api.generated.ts (自动生成)
    │
    ▼  (import type)
frontend/src/types/api.ts (再导出, 人类可读别名)
    │
    ▼  (service 函数参数/返回值)
所有 service 函数和 page 组件
```

---

## 4. API 契约层

### 4.1 设计目标

消除前后端类型不一致问题，实现：
- 后端 Pydantic 模型修改后，前端编译即可发现不兼容
- 不再需要手写 TypeScript 接口来"猜"后端返回
- 字段增删/改名/类型变更在 CI 阶段就能暴露

### 4.2 类型生成链路

```
┌─────────────────┐      ┌─────────────────┐      ┌──────────────────────┐
│ 后端 Pydantic   │ ───► │ FastAPI 自动     │ ───► │ /openapi.json        │
│ models.py       │      │ 生成 OpenAPI     │      │ (运行时 HTTP 端点)   │
└─────────────────┘      └─────────────────┘      └──────────┬───────────┘
                                                             │
                                          ┌──────────────────▼────────────┐
                                          │ fetch /openapi.json           │
                                          │ openapiTS(spec) → AST nodes  │
                                          │ astToString() → .ts file     │
                                          └──────────────────┬────────────┘
                                                             │
                                          ┌──────────────────▼────────────┐
                                          │ api.generated.ts              │
                                          │ (components.schemas.*)       │
                                          │ (paths.*)                    │
                                          │ (operations.*)               │
                                          └──────────────────┬────────────┘
                                                             │
                                          ┌──────────────────▼────────────┐
                                          │ api.ts (再导出)               │
                                          │ TaskMode, TaskInfo, ...      │
                                          │ ApiResponse<T>, WsProgress   │
                                          └──────────────────────────────┘
```

### 4.3 维护流程

**开发时（修改后端模型后）**：

```bash
# 1. 确保后端在运行
python -m web.main

# 2. 从运行中的后端生成新类型
cd frontend
npm run generate-types

# 3. 验证编译
npx tsc --noEmit --project tsconfig.app.json
```

**CI 流程**：

```bash
# 使用仓库快照（不需要后端运行）
npm run generate-types   # 从 frontend/openapi.json 读取
npm run build            # 包含 tsc 类型检查
```

**快照更新**：

```bash
# 后端运行后保存当前 schema 快照
npm run dump-openapi
git add frontend/openapi.json
```

**脚本位置**：
- `frontend/scripts/generate-types.ts` — 类型生成（优先用本地 `openapi.json` 快照，无快照时 fallback 到 `http://localhost:8000/openapi.json`）
- `frontend/scripts/dump-openapi.ts` — 从运行中的后端抓取快照

---

## 5. WebSocket 实时推送

### 5.1 协议设计

端点：`ws://localhost:8000/ws/tasks/{task_id}`

```
Client                          Server
  │                               │
  │── connect ───────────────────►│ accept()
  │◄── 当前状态快照 ──────────────│ 立即发送一次
  │                               │
  │◄── progress ──────────────────│ 每 2s 轮询
  │◄── progress ──────────────────│ (仅变化时发送)
  │◄── complete/error ────────────│ 终态后断开
```

### 5.2 消息类型

| type | 触发时机 | 携带字段 |
|------|---------|---------|
| `"progress"` | 状态或进度有变化（每 2s 检查） | `stage`, `message`, `progress` |
| `"complete"` | 任务终态（completed/failed） | `status`, `message` |
| `"error"` | 任务被删除 | `message` |

### 5.3 后端实现

- `_active_connections: dict[task_id, list[WebSocket]]` — 支持同任务多连接
- `asyncio.sleep(2)` 轮询 + 变化检测（避免无意义推送）
- `WebSocketDisconnect` 时自动清理连接

---

## 6. 静态文件服务

### 6.1 媒体文件

`GET /media/{task_id}/{filepath}` 提供任务产物目录下的任意文件访问。

**安全措施**：
- `os.path.normpath` 防目录穿越
- 检查最终路径必须在 `output_dir` 前缀内
- 403 Forbidden 拦截越权访问

### 6.2 前端生产构建

```python
# web/main.py — 自动检测
frontend_dist = os.path.join(..., "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
```

`html=True` 启用 SPA fallback：当请求不匹配任何 API 路由时，返回 `index.html`，由 react-router 接管路由。

**开发模式**：前端由 Vite dev server 独立运行（`http://localhost:5173`），通过 Vite proxy 转发 `/api` 和 `/ws` 到后端 `http://localhost:8000`。

---

## 7. 部署架构

### 7.1 开发环境

```
┌──────────────┐     ┌──────────────────┐
│ Vite Dev     │────►│ FastAPI (8000)   │
│ :5173        │proxy│ uvicorn --reload │
│ HMR + React  │◄────│                  │
└──────────────┘     └──────────────────┘
```

### 7.2 生产环境（Docker）

```
┌─────────────────────────────────────┐
│ Docker Container                    │
│                                     │
│  ┌───────────────────────────────┐  │
│  │ FastAPI (uvicorn)             │  │
│  │ ├─ API routes (:8000)        │  │
│  │ └─ Static files (frontend/)  │  │
│  └───────────────────────────────┘  │
│                                     │
│  Port mapping: 8000:8000            │
└─────────────────────────────────────┘
```

Docker 构建流程：
```dockerfile
# 1. 安装 Python 依赖
# 2. 构建前端: npm ci && npm run build
# 3. 将 frontend/dist/ 复制到容器内
# 4. FastAPI 启动后自动 mount 前端静态文件
```

### 7.3 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `UVICORN_HOST` | `0.0.0.0` | 监听地址 |
| `UVICORN_PORT` | `8000` | 监听端口 |

---

## 8. 开发工作流

### 8.1 前端开发

```bash
cd frontend
npm install
npm run dev          # Vite dev server :5173
```

Vite 配置中已设置 proxy：
```typescript
// vite.config.ts
server: {
  proxy: {
    '/api': 'http://localhost:8000',
    '/ws': { target: 'ws://localhost:8000', ws: true },
    '/media': 'http://localhost:8000',
  }
}
```

### 8.2 后端开发

```bash
# 安装依赖
pip install -r requirements.txt

# 启动后端（不含前端静态文件）
python -m web.main
# 或
uvicorn web.main:create_app --factory --reload
```

### 8.3 全栈联调

```bash
# 终端 1：启动后端
python -m web.main

# 终端 2：启动前端 dev server
cd frontend && npm run dev

# 访问 http://localhost:5173
```

### 8.4 生产构建

```bash
# 构建前端
cd frontend && npm run build    # 输出到 dist/

# 启动后端（自动 mount dist/）
python -m web.main

# 访问 http://localhost:8000 （前端 + API 同端口）
```

---

> **文档版本**：v1.0
> **更新日期**：2026-05-25
> **基于项目版本**：v1.4.0
