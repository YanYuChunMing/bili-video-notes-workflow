# 贡献指南

感谢你考虑为本项目做出贡献！本文档定义了项目的协作规范，请务必在提交代码前阅读。

---

## 目录

1. [提交信息规范（Conventional Commits）](#1-提交信息规范conventional-commits)
2. [版本号规则（Semantic Versioning）](#2-版本号规则semantic-versioning)
3. [版本发布流程](#3-版本发布流程)
4. [代码规范](#4-代码规范)
5. [提交流程](#5-提交流程)
6. [报告问题](#6-报告问题)

---

## 1. 提交信息规范（Conventional Commits）

本项目强制遵循 [Conventional Commits](https://www.conventionalcommits.org/zh-hans/v1.0.0/) 规范。每条提交信息必须符合以下格式：

```
<type>(<scope>): <简短描述>

[可选的正文]

[可选的脚注]
```

### 1.1 Type（类型）

`type` 必须为以下之一：

| Type | 说明 | 示例 |
|------|------|------|
| `feat` | 新增功能 | `feat(downloader): 添加代理支持` |
| `fix` | 修复 Bug | `fix(transcriber): 修复 CUDA DLL 缺失崩溃` |
| `docs` | 文档变更（README、注释等） | `docs: 更新快速开始指南` |
| `style` | 代码格式调整（空格、分号等，不影响逻辑） | `style: 统一缩进为 4 空格` |
| `refactor` | 代码重构（不修复 Bug 也不新增功能） | `refactor(config): 抽离路径解析逻辑` |
| `perf` | 性能优化 | `perf(screenshotter): SSIM 计算改用降采样` |
| `test` | 添加或修改测试 | `test: 添加链接解析单元测试` |
| `chore` | 构建/工具/依赖变更 | `chore: 升级 yt-dlp 最低版本要求` |
| `ci` | CI/CD 配置变更 | `ci: 添加 GitHub Actions 自动发布` |
| `revert` | 回滚某次提交 | `revert: 回滚 feat(downloader): 添加代理支持` |

### 1.2 Scope（范围）

`scope` 是可选的，用于标明本次变更影响的模块。推荐使用以下范围：

| Scope | 对应模块 |
|-------|----------|
| `downloader` | 媒体下载器 |
| `transcriber` | 语音转录器 |
| `text-cleaner` | 文字清洗器 |
| `summarizer` | 摘要生成器 |
| `mindmap` | 思维导图生成器 |
| `screenshotter` | 智能截图器 |
| `config` | 配置管理 |
| `link-parser` | 链接解析器 |
| `utils` | 工具函数 |
| `markdown` | Markdown 构建器 |
| `video-splitter` | 视频分段器 |
| `cli` | 命令行入口 |
| `docs` | 文档 |

### 1.3 描述规则

- 使用**中文**写描述（本项目面向中文用户）
- 使用祈使句，不加句号
- 首行不超过 **72 个字符**
- 如果变更较大，可以在正文中详细说明"为什么"以及"与之前有什么不同"

### 1.4 正确示例 ✅

```bash
# 新增功能
git commit -m "feat(downloader): 添加 HTTP 代理配置支持"

# Bug 修复
git commit -m "fix(transcriber): 修复 CUDA 13 环境下 cublas DLL 加载失败"

# 文档更新
git commit -m "docs: 补充 Windows 下 ffmpeg 的安装教程"

# 重构
git commit -m "refactor(config): 将路径解析抽离为独立函数"

# 带正文的提交（用 -m 多次指定）
git commit -m "fix(screenshotter): 修复中文路径截图写入失败" -m "
> 将 cv2.imwrite 替换为 cv2.imencode + Python open(wb)，
> 解决 Windows 下 OpenCV 对非 ASCII 路径的兼容性问题。"
```

### 1.5 错误示例 ❌

```bash
# ❌ 没有 type
git commit -m "修复了一个bug"

# ❌ type 不规范
git commit -m "update: 更新readme"
git commit -m "bugfix: xxx"

# ❌ 首行太长
git commit -m "feat(downloader): 添加了对HTTP代理、SOCKS5代理、自定义请求头和Cookie文件导入的全面支持"

# ❌ 描述太随意
git commit -m "feat: 改了一下"
```

---

## 2. 版本号规则（Semantic Versioning）

版本号格式：`MAJOR.MINOR.PATCH`（如 `1.2.3`）

| 版本段 | 何时递增 | 示例场景 |
|--------|----------|----------|
| **MAJOR** | 做了不兼容的 API 修改 | 移除某个公开函数、修改配置文件格式 |
| **MINOR** | 新增了向下兼容的功能 | 新增代理支持、新增转录后端 |
| **PATCH** | 做了向下兼容的 Bug 修复 | 修复路径问题、修复崩溃 Bug |

递增规则：
- `MINOR` 递增时，`PATCH` 归零
- `MAJOR` 递增时，`MINOR` 和 `PATCH` 归零

---

## 3. 版本发布流程

### Step 1：确保代码就绪

```bash
# 运行代码质量检查
python _check.py

# 确认没有已知问题
```

### Step 2：更新 CHANGELOG.md

按照 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 格式，在新版本标题下归类变更：

- `### Added` — 新增功能
- `### Changed` — 功能变更
- `### Deprecated` — 即将废弃
- `### Removed` — 已移除
- `### Fixed` — Bug 修复
- `### Security` — 安全修复

### Step 3：提交并打 Tag

```bash
# 提交 CHANGELOG 更新
git add CHANGELOG.md
git commit -m "chore(release): 准备发布 v1.2.0"

# 打带注释的版本标签
git tag -a v1.2.0 -m "v1.2.0: 新增代理支持与 GTP-4o 转录后端"

# 推送代码和标签
git push origin main
git push origin v1.2.0
```

### Step 4：创建 GitHub Release

在 GitHub Releases 页面基于 Tag 创建 Release，将 CHANGELOG 中该版本的内容粘贴到 Release Notes 中。

---

## 4. 代码规范

- 遵循 [PEP 8](https://peps.python.org/pep-0008/) Python 代码风格
- 使用 `logging` 模块进行日志记录，**禁止**使用 `print()` 作为日志输出
- 所有公开函数需添加**类型标注**（Type Hints）
- 代码应自解释，不添加无意义的注释
- 新增功能模块需同步更新 `PROJECT_FRAMEWORK.md` 中的对应章节

### 提交前检查

```bash
python _check.py
```

该脚本执行：
1. **pyright** — 全项目静态类型检查
2. **AST** — 编译语法检查

---

## 5. 提交流程

```
1. Fork 本仓库
   │
2. 创建功能分支
   git checkout -b feat/my-feature
   │
3. 编写代码 + 自测
   │
4. 运行 python _check.py 确保通过
   │
5. 提交（遵循 Conventional Commits）
   git commit -m "feat(module): 描述你的变更"
   │
6. 推送到你的 Fork
   git push origin feat/my-feature
   │
7. 提交 Pull Request 到 main 分支
```

**分支命名建议**：

| 前缀 | 用途 | 示例 |
|------|------|------|
| `feat/` | 新功能 | `feat/proxy-support` |
| `fix/` | Bug 修复 | `fix/cuda-dll-crash` |
| `docs/` | 文档 | `docs/readme-rewrite` |
| `refactor/` | 重构 | `refactor/config-loader` |
| `chore/` | 杂项 | `chore/update-deps` |

---

## 6. 报告问题

如果你发现了 Bug 或有功能建议，请在 GitHub Issues 中提交。请包含以下信息：

1. **运行模式**：`basic` 还是 `with_images`
2. **Python 版本**：`python --version` 的输出
3. **操作系统**：Windows / macOS / Linux 及版本
4. **错误日志**：位于 `logs/` 目录下的完整日志文件
5. **复现步骤**：尽可能详细地描述如何触发该问题

---

> 遵循这些规范，我们一起打造高质量的开源项目！🎉
