# bili-video-notes-workflow

> 🎬 把 B站视频变成学习笔记 —— 不用动手，让程序帮你写！

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.2.0-blue)](CHANGELOG.md)

---

## 📑 目录

- [🤔 这是什么？](#-这是什么)
- [🧭 我应该看哪里？](#-我应该看哪里)
- [🐳 Docker 一键部署（推荐！）](#-docker-一键部署推荐跳过所有环境配置)
  - [第零步：从 GitHub 下载项目代码](#第零步从-github-下载项目代码)
  - [第一步：安装 Docker（系统要求）](#第一步安装-docker系统要求)
  - [第二步：准备配置文件](#第二步准备配置文件-1)
  - [第三步：构建 Docker 镜像](#第三步构建-docker-镜像)
  - [第四步：运行！](#第四步运行)
  - [🖥️ 有 NVIDIA 显卡？用 GPU 加速版](#️-有-nvidia-显卡用-gpu-加速版转录快-10-倍)
  - [🧹 清理 / 更新 / FAQ](#-清理--更新--docker-常见问题-faq)
- [🚀 从零开始的完整部署指南](#-从零开始的完整部署指南)
  - [第一步：检查 / 安装 Python](#第一步检查--安装-python)
    - [🔍 先检查有没有装过 Python](#-先检查你的电脑有没有装过-python)
    - [🪟 Windows 系统安装 Python](#-python-安装教程--windows-系统)
    - [🍎 macOS 系统安装 Python](#-python-安装教程--macos-系统)
    - [🐧 Linux 系统安装 Python](#-python-安装教程--linux-系统)
  - [第二步：检查 / 安装 ffmpeg](#第二步检查--安装-ffmpeg)
    - [🔍 先检查有没有装过 ffmpeg](#-先检查你的电脑有没有装过-ffmpeg)
    - [🪟 Windows 系统安装 ffmpeg](#-ffmpeg-安装教程--windows-系统)
    - [🍎 macOS 系统安装 ffmpeg](#-ffmpeg-安装教程--macos-系统)
    - [🐧 Linux 系统安装 ffmpeg](#-ffmpeg-安装教程--linux-系统)
  - [第三步：下载项目代码](#第三步下载项目代码)
    - [✅ ZIP 下载（推荐新手）](#-方式二直接下载-zip推荐最简单)
    - [💻 Git 命令下载](#-方式一用-git-命令下载)
  - [第四步：创建虚拟环境并安装依赖](#第四步创建虚拟环境并安装所有依赖)
    - [4.1 创建虚拟环境](#41-创建虚拟环境)
    - [4.2 激活虚拟环境](#42-激活虚拟环境)
    - [4.3 安装 Python 依赖包](#43-安装-python-依赖包)
    - [4.4 安装 yt-dlp](#44-安装-yt-dlpb站视频下载工具)
    - [4.5 确认安装成功](#45-确认安装成功)
  - [第五步：创建配置文件](#第五步创建配置文件)
- [🔑 DeepSeek 账号注册与 API 密钥获取](#-deepseek-账号注册与-api-密钥获取)
  - [为什么要注册 DeepSeek？](#为什么要注册-deepseek)
  - [Step 1：打开 DeepSeek 官网并注册账号](#step-1打开-deepseek-官网并注册账号)
  - [Step 2：登录并进入 API 管理后台](#step-2登录并进入-api-管理后台)
  - [Step 3：创建 API Key（密钥）](#step-3创建-api-key密钥)
  - [Step 4：把密钥写入项目配置文件](#step-4把密钥写入项目配置文件)
  - [没有 API Key 能用吗？](#没有-api-key-能用吗)
- [▶️ 运行你的第一个视频](#️-运行你的第一个视频)
  - [添加 B站链接](#添加-b站链接)
  - [启动程序](#启动程序)
  - [看懂运行日志](#看懂运行日志)
  - [要多久？](#要多久)
- [📁 查看成果](#-查看成果)
- [🎮 运行模式说明](#-运行模式说明)
- [📂 项目文件结构](#-项目文件结构)
- [❓ 常见问题排查](#-常见问题排查)
- [⚙️ 配置说明（进阶）](#️-配置说明进阶)
- [📊 技术栈](#-技术栈)
- [⚠️ 已知限制](#️-已知限制)
- [📚 更多文档](#-更多文档)
- [📄 License](#-license)

---

## 🤔 这是什么？

**你给它一个 B站视频链接，它自动帮你生成学习笔记 + 思维导图。**

比如你有一期讲 Go 语言的 B站教程：

```
https://www.bilibili.com/video/BV1eRrABqE7P
```

把链接放进去跑一遍，过一会儿你就得到：

| # | 产物 | 文件名 | 有什么用 |
|---|------|--------|----------|
| 1 | 📝 纯文字稿 | `transcript.txt` | 视频说的每一个字转成文字 |
| 2 | ✍️ 带标点文字稿 | `transcript_with_punct.txt` | AI 帮你加好标点、分好段落 |
| 3 | 📖 学习笔记 | `summary.md` | AI 提炼的知识要点，复习就看它 |
| 4 | 🧠 思维导图 | `mindmap.html` | 双击用浏览器打开，知识结构一目了然 |
| 5 | 🖼️ 图文笔记（可选） | `transcript_with_images.md` | 截图 + 文字，做教程笔记绝配 |

**数据是怎么流转的：**

```
B站链接 → 下载音频 → Whisper 语音转文字 → DeepSeek AI 加标点/写摘要/画导图 → 你的笔记
```

---

## 🧭 我应该看哪里？

| 你的情况 | 看这里 |
|----------|--------|
| 🐳 不想装 Python、ffmpeg 各种环境 | → [🐳 Docker 一键部署（推荐！）](#-docker-一键部署推荐跳过所有环境配置) |
| 🔰 电脑新手，从没装过 Python | → [🚀 从零开始的完整部署指南](#-从零开始的完整部署指南) |
| 💻 环境已配好，想直接跑 | → [▶️ 运行你的第一个视频](#️-运行你的第一个视频) |
| 🆘 跑出错了 | → [❓ 常见问题排查](#-常见问题排查) |
| 🔧 想看源码 | → [PROJECT_FRAMEWORK.md](PROJECT_FRAMEWORK.md) |

---

## 🐳 Docker 一键部署（推荐！跳过所有环境配置）

> 🎯 **这是最快最简单的上手方式。** 不用装 Python，不用装 ffmpeg，不用创建虚拟环境，不用解决各种依赖冲突。Docker 帮你把所有东西打包好了，**一条命令就能跑。**

---

### 第零步：从 GitHub 下载项目代码

> 📌 整个项目只有源代码在 GitHub 上（Dockerfile、Python 脚本、配置文件等等）。**Docker 镜像本身不需要从 GitHub 下载**——你本地一键构建，自动拉取所有依赖。

打开浏览器，访问项目主页：

> 🔗 **项目地址：https://github.com/YanYuChunMing/bili-video-notes-workflow**

你会看到这样的页面布局：

```
┌──────────────────────────────────────────────────────────┐
│  YanYuChunMing / bili-video-notes-workflow  ⭐ Star      │
│                                                          │
│  🎬 把 B站视频变成学习笔记 ...                            │
│                                                          │
│  ┌─────────┐  ┌─────────────────────────────────────────┐ │
│  │  main   │  │  ↕️ 切换分支 / 标签            ⬇ Code  │ │
│  │  branch │  │                               (绿色按钮) │ │
│  └─────────┘  └─────────────────────────────────────────┘ │
│                                                          │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  📄 README.md           (网页版说明文档)              │ │
│  │  📄 CHANGELOG.md        (版本更新日志)               │ │
│  │  📄 Dockerfile          (Docker 镜像定义)            │ │
│  │  📄 docker-compose.yml  ...                          │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  📁 Releases  (右侧边栏 ← 点这里看历史版本)          │ │
│  └──────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

#### 下载方式一：点击绿色「⬇ Code」→ Download ZIP（推荐新手）

在项目主页右上角（README 上方），找到绿色按钮 **「⬇ Code」**，点击它：

```
┌──────────────────────────┐
│  Clone                   │
│                          │
│  ○ HTTPS                 │
│  ○ SSH                   │
│                          │
│  https://github.com/...  │
│  ┌──────────────────┐    │
│  │ 📋 复制链接       │    │
│  └──────────────────┘    │
│                          │
│  ────────────────────    │
│  Download ZIP      ← 点  │
│                          │
└──────────────────────────┘
```

点击 **「Download ZIP」**，浏览器开始下载压缩包（约几百 KB）。下载完成后：

1. 在"下载"文件夹找到 `bili-video-notes-workflow-main.zip`
2. **右键 → 全部提取** → 解压到你想要的位置（如 `D:\bili-video-notes-workflow`）
3. 解压后你会看到 `main.py`、`Dockerfile`、`docker-compose.yml`、`links.txt` 等文件

#### 下载方式二：通过 Releases 页面下载指定版本

如果你想下载某个历史版本：

1. 在项目主页右侧边栏，找到 **「Releases」** 链接并点击
2. 进入 Releases 页面后，你会看到按时间倒序排列的版本列表：

```
┌──────────────────────────────────────────────────────────┐
│  Releases                                                 │
│                                                          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  v1.2.0                        ⬆️ Latest            │ │
│  │  @YanYuChunMing released this on 5月22日             │ │
│  │                                                     │ │
│  │  ## [1.2.0] - 2026-05-22                           │ │
│  │  ### Added                                         │ │
│  │  #### Docker 容器化支持 (CPU + GPU 双版本) ...      │ │
│  │                                                     │ │
│  │  ┌─────────────────────────────────────────────┐    │ │
│  │  │  Assets                                      │    │ │
│  │  │                                             │    │ │
│  │  │  📦 Source code (zip)  ← 下载这个           │    │ │
│  │  │  📦 Source code (tar.gz)                    │    │ │
│  │  └─────────────────────────────────────────────┘    │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │  v1.1.0                           (历史版本)         │ │
│  │  ...                                                │ │
│  └─────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

3. 在最新版本（最上面那个）的 **「Assets」** 区域，点击 **「Source code (zip)」** 下载
4. 下载后解压即可，和方式一一样

> 💡 **省事小窍门**：在解压后的项目文件夹地址栏里直接输入 `powershell` 然后回车，终端自动定位到当前目录，连 cd 都不用打。

---

### 第一步：安装 Docker（系统要求）

#### 系统要求速查

| 系统 | 版本要求 | 内存建议 | 磁盘空间 | Docker 类型 |
|------|----------|----------|----------|-------------|
| 🪟 Windows 10/11 | 专业版/企业版/教育版 | ≥ 8GB | ≥ 10GB 空闲 | Docker Desktop |
| 🍎 macOS | macOS 12 (Monterey)+ | ≥ 8GB | ≥ 10GB 空闲 | Docker Desktop |
| 🐧 Ubuntu/Debian | 20.04+ | ≥ 4GB | ≥ 10GB 空闲 | Docker Engine |
| 🐧 Fedora | 38+ | ≥ 4GB | ≥ 10GB 空闲 | Docker Engine |

> ⚠️ Windows 家庭版用户需要启用 WSL2。安装脚本会自动处理，如失败则参照下方"常见问题"第 2 条。

#### 一键安装 Docker

项目内置了各平台的一键安装脚本，无需手动去 Docker 官网下载：

| 你的系统 | 操作 |
|----------|------|
| 🪟 Windows | 在项目文件夹中，**右键 `docker_install.ps1`** → 选择「使用 PowerShell 运行」 |
| 🍎 macOS | 打开终端，cd 到项目文件夹，执行 `bash docker_install.sh` |
| 🐧 Linux | 打开终端，cd 到项目文件夹，执行 `bash docker_install.sh` |

脚本会自动检测你是否已经装过 Docker，装了就跳过，没装就自动下载安装。

#### Windows 安装后

1. **必须重启电脑**
2. 重启后在开始菜单搜索 **「Docker Desktop」**，点击启动
3. 首次启动会弹出服务协议，点 **「Accept」** 即可
4. 等任务栏右下角出现 **🐳 鲸鱼图标**（静止不动几秒后图标稳定），说明 Docker 启动成功

#### macOS 安装后

1. 在「应用程序」文件夹找到 **Docker**，双击启动
2. 首次启动需要输入 Mac 开机密码（授权系统级服务）
3. 菜单栏顶部出现 **🐳 鲸鱼图标** → 点击 → 看到 "Docker Desktop is running" = 启动成功

#### Linux 安装后

```bash
# 确认 Docker 服务正在运行
sudo systemctl status docker

# 如果没跑起来，启动它
sudo systemctl start docker

# 将当前用户加入 docker 组（不用每次输 sudo）
sudo usermod -aG docker $USER
# 然后注销重新登录使配置生效
```

#### 验证 Docker 安装

打开终端，输入：

```bash
docker --version
```

如果看到类似 `Docker version 27.x.x, build ...` 就说明装好了。

再确认 compose 插件（用于 `docker compose` 命令）：

```bash
docker compose version
```

看到 `Docker Compose version v2.x.x` 即可。

#### Docker 安装常见问题

**Q：Windows 双击 `docker_install.ps1` 报 "无法加载，因为在此系统上禁止运行脚本"？**

以管理员身份打开 PowerShell，执行：

```bash
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

然后重新右键运行 `docker_install.ps1`。

**Q：Windows 启动 Docker Desktop 后一直转圈，最后报 "Docker Desktop - Unexpected WSL error"？**

以管理员身份打开 PowerShell，执行：

```bash
wsl --install
```

等待安装完成，**重启电脑**，然后再打开 Docker Desktop。

**Q：安装脚本下载 Docker 很慢？**

脚本已内置国内加速逻辑。如仍很慢：

- Windows：直接去 https://www.docker.com/products/docker-desktop/ 手动下载
- macOS：直接去 https://www.docker.com/products/docker-desktop/ 手动下载（区分 Intel / Apple Silicon）
- Linux：换阿里云镜像：`curl -fsSL https://get.docker.com | bash -s docker --mirror Aliyun`

**Q：Linux 执行 `docker` 命令提示 `permission denied`？**

```bash
sudo usermod -aG docker $USER
newgrp docker    # 当前终端立即生效
```

---

### 第二步：准备配置文件

项目文件夹里操作：

```bash
# 复制配置模板
copy config.example.toml config.toml

# 复制密钥模板
copy .env.example .env
```

> Mac / Linux 用 `cp` 代替 `copy`：`cp config.example.toml config.toml`

用记事本打开 `.env`，把 `sk-your-api-key-here` 替换成你的真实 DeepSeek API 密钥。

> 💡 不知道怎么获取 API 密钥？看 [🔑 DeepSeek 账号注册与 API 密钥获取](#-deepseek-账号注册与-api-密钥获取)。

在 `links.txt` 里每行粘贴一个 B站视频链接，保存。

---

### 第三步：构建 Docker 镜像

在项目文件夹里打开终端，执行：

```bash
docker compose build
```

```
（终端输出示意）
────────────────────────────────────────────
[+] Building 180.5s (12/12) FINISHED
 => [1/5] FROM python:3.12-slim
 => [2/5] RUN apt-get install ffmpeg
 => [3/5] COPY requirements.txt .
 => [4/5] RUN pip install -r requirements.txt
 => [5/5] COPY . .
 => exporting to image
 => naming to bili-video-notes:latest
────────────────────────────────────────────
```

第一次构建大约 **3～8 分钟**（取决于网速）。以后代码更新后重建只需几秒钟（复用缓存）。

---

### 第四步：运行！

```bash
docker compose run --rm bili-video --task basic_test
```

程序开始跑，和手动部署完全一样的效果：

```
=== 启动任务: basic_test ===
模式: basic
链接文件: links.txt
[1] ===== 开始处理: https://www.bilibili.com/video/xxx =====
  ↓ 正在下载音频（yt-dlp）...
  ↓ 正在语音转录（Whisper）...
  ↓ AI 正在添加标点...
  ↓ AI 正在生成笔记摘要...
  ↓ AI 正在生成思维导图...
[1] ===== 处理完成: xxx =====
```

**你没装过一行 Python 环境，只是装了 Docker。**

#### 运行其他模式

```bash
# 图文笔记模式（下载视频 + 智能截图）
docker compose run --rm bili-video --task with_images_test

# 直接指定链接文件和模式
docker compose run --rm bili-video --input links.txt --mode basic
```

成果在项目文件夹的 `outputs/` 目录，和手动部署完全一样。

---

### 🖥️ 有 NVIDIA 显卡？用 GPU 加速版（转录快 10 倍）

| 模式 | 转录 20 分钟视频耗时 | 适用 |
|------|----------------------|------|
| 普通 Docker（CPU） | 10～20 分钟 | 所有电脑 |
| GPU Docker | **1～3 分钟** | 有 NVIDIA 显卡 |

#### 前置要求

1. **NVIDIA 显卡**（GTX 750 以上，显存 ≥ 4GB 推荐）
2. **NVIDIA 驱动**（装过 GeForce Experience 的就没问题）
3. **NVIDIA Container Toolkit**（只需装一次）

> **Windows**：装 Docker Desktop 时已自动包含，无需额外操作。
>
> **Linux**：需要单独装。复制以下全部命令到终端执行：
> ```bash
> # Ubuntu / Debian
> curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
> curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
>   sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
>   sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
> sudo apt-get update
> sudo apt-get install -y nvidia-container-toolkit
> sudo systemctl restart docker
> ```
>
> **macOS**：Mac 上 Docker 不支持直通 GPU，请用普通 CPU 版。

#### 构建 GPU 镜像

```bash
docker compose --profile gpu build bili-video-gpu
```

首次构建会下载 CUDA 基础镜像（约 2.5GB）+ 依赖包，共约 5～10 分钟。

#### 运行 GPU 版

```bash
# 基础模式
docker compose --profile gpu run --rm bili-video-gpu --task basic_test

# 图文笔记
docker compose --profile gpu run --rm bili-video-gpu --task with_images_test
```

#### 怎么确认在用 GPU？

看日志中是否出现：

```
Whisper 模型已加载到 cuda
```

如果出现 `running on cpu`，检查显卡驱动和 nvidia-container-toolkit。

> 💡 GPU 版和 CPU 版镜像相互独立，互不影响。可同时构建、按需切换。

---

### 🧹 清理 / 更新 / Docker 常见问题 (FAQ)

#### 更新项目代码后

```bash
git pull                 # 拉取最新代码（或用 Download ZIP 重新下载覆盖）
docker compose build     # 重新构建镜像（依赖有更新时）
docker compose run --rm bili-video --task basic_test
```

> 💡 只改了 `.py` 源码文件？`docker compose build` 秒级完成。只有改了 `requirements.txt` 才会重新下载依赖。

#### 磁盘空间不足？清理 Docker

```bash
# 删掉项目镜像（释放约 2~3GB）
docker compose down --rmi all

# 连带 GPU 镜像一起删
docker compose --profile gpu down --rmi all

# Docker 整体垃圾回收
docker system prune -a
```

#### Q：`docker compose build` 报 `ERROR: Cannot connect to the Docker daemon`？

Docker Desktop 没启动。Windows：开始菜单搜 "Docker Desktop" 打开。Mac：应用程序里找到 Docker 打开。看到鲸鱼图标即启动成功。

#### Q：`docker compose build` 下载依赖很慢？

Dockerfile 中 pip 已配置清华镜像源（`pypi.tuna.tsinghua.edu.cn`），国内用户无需额外设置。

#### Q：容器跑完输出文件在哪？

在**宿主机**（你的电脑）项目文件夹的 `outputs/` 里。`docker-compose.yml` 里已配置 `volumes` 挂载，容器内产出的文件直接写入你的本地磁盘。

#### Q：想把产物放到别的目录？

编辑 `docker-compose.yml`，把 `./outputs:/app/outputs` 中的 `./outputs` 改成你想要的路径，比如 `D:\my_notes:/app/outputs`。

#### Q：能不能后台跑？

```bash
docker compose run --rm -d bili-video --task basic_test
```

> ⚠️ 不推荐，因为你看不到实时日志，不知道跑完没有。

---

> 💡 **原理简述**：Docker 就像一个"轻量级虚拟机"，它在一个隔离的容器里装好了 Python、ffmpeg、所有依赖库，然后运行你的项目代码。你电脑上不需要装任何东西（除了 Docker 本身），用完删掉镜像，电脑干干净净。

---

## 🚀 从零开始的完整部署指南

> ⏱️ 全新电脑从头开始，全程约 **15～30 分钟**（大部分时间在等待下载）。
>
> 📌 你不需要任何编程知识。每一步都有截图描述，跟着做就行。所有命令都**直接复制粘贴**到黑色窗口里按回车，不要手打。

在开始之前，先认识一下你要用的工具：

> **「终端」是什么？** 就是你电脑上一个黑底白字的窗口，你在里面打字告诉电脑做什么。
>
> **怎么打开？** 按键盘上的 `Win` 键 + `R` 键 → 输入 `powershell` → 点确定。看到黑色窗口就对了。
>
> **怎么用？** 本文所有灰色代码块里的文字，复制粘贴到终端里，按回车。**不要手打，复制粘贴不出错。**

---

### 第一步：检查 / 安装 Python

> Python 是运行这个程序需要的底层软件。你可以把它理解成"运行这个程序必须装的驱动"，就像要打游戏需要 Steam 一样。

---

#### 🔍 先检查你的电脑有没有装过 Python

打开终端，复制下面这行命令，粘贴进去，按回车：

```bash
python --version
```

看看屏幕显示什么：

**✅ 如果显示类似下面这样的文字（数字 ≥ 3.10 就可以）：**

```
Python 3.12.7
```

→ 说明 Python 已经装好了！**直接跳到 [第二步：安装 ffmpeg](#第二步检查--安装-ffmpeg) 继续。**

**❌ 如果显示这样的错误提示：**

```
'python' 不是内部或外部命令，也不是可运行的程序或批处理文件。
```

→ 说明你的电脑还没装 Python。**跟着下面的教程一步一步装，大约 5 分钟。**

---

#### 🪟 Python 安装教程 —— Windows 系统

##### 1. 下载 Python 安装包

打开你电脑上的浏览器（Edge、Chrome 随便哪个都行），在地址栏输入下面这个链接，然后回车：

> 🔗 **下载地址：https://www.python.org/downloads/**

你会看到一个蓝色+白色为主色调的网页，这就是 Python 的官方网站。页面正中间有个**醒目的黄色大按钮**，上面写着类似 `Download Python 3.12.7` 的文字（具体数字可能更新，没关系）。

```
┌─────────────────────────────────────────────────┐
│                python.org                        │
│                                                  │
│         ┌─────────────────────────┐              │
│         │                         │              │
│         │   Download Python       │  ← 黄色大按钮 │
│         │      3.12.7             │              │
│         │                         │              │
│         └─────────────────────────┘              │
│                                                  │
└─────────────────────────────────────────────────┘
```

**点击这个黄色按钮**，浏览器就开始下载了。下载的文件名叫 `python-3.12.7-amd64.exe`（大约 25MB），会保存在你电脑的"下载"文件夹里。

> 💡 如果不确定选哪个，看这里：绝大多数 Windows 电脑选 **Windows installer (64-bit)** 就对了。页面往下滚一点能看到"Files"表格，里面也有同样的下载。

---

##### 2. 运行安装程序

找到刚才下载的 `python-3.12.7-amd64.exe` 文件（通常在桌面左下角"下载"文件夹、或者浏览器底部下载栏），**双击打开它**。

你会看到一个蓝色的安装界面：

```
┌──────────────────────────────────────────┐
│  Python 3.12.7 (64-bit) Setup            │
│                                          │
│  ┌──────────────────────────────────┐    │
│  │  Install Now                     │    │
│  │  Customize installation          │    │
│  └──────────────────────────────────┘    │
│                                          │
│  ☑ Install launcher for all users       │
│  ☐ Add Python 3.12 to PATH   ← ⚠️       │
│                                          │
│         [Cancel]                         │
└──────────────────────────────────────────┘
```

> ⚠️ ⚠️ ⚠️ **这是整个安装过程中最关键的一步！千万别漏掉！**

你必须在界面底部找到 `Add Python 3.12 to PATH` 这个选项，**点击它前面的小方框，把它勾上**（打 ✓）。

```
  ☑ Add Python 3.12 to PATH   ← 必须勾上！
```

**为什么一定要勾？** 勾了之后，你才能在终端里输入 `python` 命令让电脑识别。不勾的话，后面所有步骤都会报错"找不到 python"，你又得重新装一遍。**99% 的报错都源自忘了勾这一下。**

---

##### 3. 开始安装

勾好那个选项之后，点击上面的 **「Install Now」**（现在安装）按钮。

```
┌──────────────────────────────────────────┐
│  Python 3.12.7 (64-bit) Setup            │
│                                          │
│  ████████████████░░░░░░░  65%           │
│                                          │
│  Installing...                           │
│  Adding Python to PATH...               │
│                                          │
└──────────────────────────────────────────┘
```

安装过程会持续 **1～2 分钟**。屏幕上的进度条会慢慢走完，中间可能闪过一个黑色窗口（那是正常的，不用管）。

---

##### 4. 安装完成

进度条走满后，你会看到这个界面：

```
┌──────────────────────────────────────────┐
│  Python 3.12.7 (64-bit) Setup            │
│                                          │
│       Setup was successful               │
│                                          │
│  Thank you for installing Python!        │
│                                          │
│         [Close]                          │
└──────────────────────────────────────────┘
```

点击 **「Close」** 关闭窗口。

---

##### 5. 验证安装

**重要：现在把终端窗口关掉，重新打开一个新终端。**（Windows 装完软件后需要重开终端才能识别新的命令。）

在新终端里输入：

```bash
python --version
```

按回车。你应该看到：

```
Python 3.12.7
```

🎉 **Python 安装成功！** 继续看 [第二步：安装 ffmpeg](#第二步检查--安装-ffmpeg) 吧。

> 如果这里还是报"不是内部或外部命令"，说明第 2 步的 `Add Python to PATH` 忘了勾。解决办法：在 Windows 搜索栏输入"应用和功能" → 找到 Python → 点击"修改" → 重新走一遍安装流程，这次一定勾上。

---

#### 🍎 Python 安装教程 —— macOS 系统

##### 1. 下载

浏览器打开下面这个链接：

> 🔗 **下载地址：https://www.python.org/downloads/macos/**

页面会自动识别你用的是 Mac，推荐最新的 macOS 安装包。点击那个黄色下载按钮，下载 `.pkg` 文件。

> 或者用 Homebrew：`brew install python@3.12`

##### 2. 安装

双击下载的 `.pkg` 文件 → 出现安装向导 → 一路点"继续"、"同意" → 输入你的 Mac 开机密码 → 等待安装完成。

```
┌─────────────────────────────────────┐
│  安装 Python                        │
│                                     │
│  欢迎使用 Python 安装器             │
│                                     │
│  [继续]                             │
│                                     │
│  （一路点继续就行，不用改任何选项）  │
└─────────────────────────────────────┘
```

##### 3. 验证

装完后，打开 Mac 的「终端」App（在"启动台" → "其他"文件夹里），输入：

```bash
python3 --version
```

看到 `Python 3.12.x` 就成功了。

> 📌 Mac 上的命令是 `python3`（有一个 3），不是 `python`。本文后面所有用到 `python` 的地方，Mac 用户请替换成 `python3`。

---

#### 🐧 Python 安装教程 —— Linux 系统

大多数 Linux 发行版已经自带了 Python。先检查一下：

```bash
python3 --version
```

如果显示版本号 ≥ 3.10，直接跳过。如果没有或版本太低：

**Ubuntu / Debian：**

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

**Fedora：**

```bash
sudo dnf install python3 python3-pip
```

**Arch：**

```bash
sudo pacman -S python python-pip
```

装完后输入 `python3 --version` 验证。

---

### 第二步：检查 / 安装 ffmpeg

> ffmpeg 是一个处理音视频的工具。你不需要知道它怎么工作——只要知道我们的程序靠它来把视频里的声音单独提取出来。

---

#### 🔍 先检查你的电脑有没有装过 ffmpeg

打开终端，输入：

```bash
ffmpeg -version
```

按回车。

**✅ 如果屏幕刷出一大段文字，开头类似这样：**

```
ffmpeg version 7.0.2-essentials_build-www.gyan.dev
Copyright (c) 2000-2024 the FFmpeg developers
...
```

→ 说明 ffmpeg 已经装好了！**直接跳到 [第三步：下载项目代码](#第三步下载项目代码) 继续。**

**❌ 如果显示这样的错误：**

```
'ffmpeg' 不是内部或外部命令，也不是可运行的程序或批处理文件。
```

→ 说明还没装。**跟着下面教程装，大约 5 分钟。**

---

#### 🪟 ffmpeg 安装教程 —— Windows 系统

ffmpeg 在 Windows 上的安装分为两大步：① 下载解压 ② 配置环境变量。很多人卡在第②步，这次我会讲得非常细。

---

##### 第一部分：下载并解压 ffmpeg

**① 打开下载页面**

打开浏览器，在地址栏输入下面这个链接，回车：

> 🔗 **下载页面：https://www.gyan.dev/ffmpeg/builds/**

你会看到 BtbN（gyan.dev）的 ffmpeg Windows 编译发布页面。

```
┌──────────────────────────────────────────────┐
│  gyan.dev / FFmpeg Builds                    │
│                                              │
│  release builds                               │
│                                              │
│  ┌─────────────────────────────────────┐     │
│  │ ffmpeg-release-essentials.zip       │ ←   │
│  │ (约 30 MB)                          │     │
│  │ 文件名旁边有个下载链接               │     │
│  └─────────────────────────────────────┘     │
│                                              │
│  ┌─────────────────────────────────────┐     │
│  │ ffmpeg-release-full.7z              │     │
│  │ (约 70 MB，完整版，不需要这个)       │     │
│  └─────────────────────────────────────┘     │
└──────────────────────────────────────────────┘
```

**② 确认你下载的是哪个文件**

| 文件名 | 大小 | 要下吗？ |
|--------|------|----------|
| `ffmpeg-release-essentials.zip` | ≈ 30 MB | ✅ **下这个！** |
| `ffmpeg-release-full.7z` | ≈ 70 MB | ❌ 太大了，不需要 |

点击 **`ffmpeg-release-essentials.zip`** 旁边的链接开始下载。

> 💡 如果你不小心进了一个文件列表页面（有很多文件的那种），找 `ffmpeg-release-essentials.zip` 点击就行。或者用这个直链：
>
> 🔗 **直链下载（备用）：https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip**

**③ 解压到 C 盘**

下载完成后，在"下载"文件夹里找到 `ffmpeg-release-essentials.zip`。

```
📁 下载
  └── ffmpeg-release-essentials.zip   ← 找到它
```

**右键点击这个 zip 文件 → 选择「全部提取」或「解压全部」：**

```
┌──────────────────────────────────┐
│  提取压缩(Zipped)文件夹           │
│                                  │
│  选择一个目标并提取文件           │
│                                  │
│  文件将被提取到这个文件夹：        │
│  ┌────────────────────────────┐  │
│  │ C:\ffmpeg                  │  │ ← 改成这个
│  └────────────────────────────┘  │
│                        [浏览...]  │
│                                  │
│  ☐ 完成时显示提取的文件           │
│                                  │
│         [提取]                    │
└──────────────────────────────────┘
```

在"文件将被提取到这个文件夹"那一栏，删掉原来的路径，输入 **`C:\ffmpeg`**，然后点「提取」。

等几秒钟解压完成。现在打开 C 盘，你应该能看到：

```
C:\
└── ffmpeg/
    ├── bin/           ← 这个文件夹很重要！
    │   ├── ffmpeg.exe
    │   ├── ffprobe.exe
    │   └── ...
    ├── doc/
    ├── presets/
    └── LICENSE
```

> 📌 记住 `C:\ffmpeg\bin` 这个路径，下一步要用。最好现在就复制下来（选中 → Ctrl+C）。

---

##### 第二部分：配置环境变量（让终端能找到 ffmpeg）

这一步是**整个部署过程中最容易出错的一步**，请严格按照顺序操作。

> **为什么要做这一步？** 你现在已经把 ffmpeg 下载到 `C:\ffmpeg\bin` 里了，但你的终端还不知道它在哪。"配置环境变量"就是告诉终端："嘿，以后我在终端里输入 `ffmpeg` 的时候，你去 `C:\ffmpeg\bin` 这个文件夹里找。"

**① 打开系统设置**

按键盘上的 `Win` 键（左下角那个 Windows 图标键），直接打字输入 **"环境变量"** 四个字。

```
┌──────────────────────────┐
│  开始菜单                │
│                          │
│  ┌──────────────────┐    │
│  │ 环境变量 ✏️       │    │
│  └──────────────────┘    │
│                          │
│  最佳匹配:               │
│  📁 编辑系统环境变量     │ ← 点击这个
│                          │
└──────────────────────────┘
```

点击搜索结果里的 **「编辑系统环境变量」**。

**② 弹出「系统属性」窗口**

```
┌────────────────────────────────────┐
│  系统属性                          │
│                                    │
│  计算机名 | 硬件 | 高级 | 远程 ...  │
│  ─────────────────────────────     │
│                                    │
│  性能                              │
│  视觉效果，处理器计划...            │
│                                    │
│  用户配置文件                      │
│  与登录帐户相关的桌面设置           │
│                                    │
│  启动和故障恢复                    │
│  系统启动、系统故障和调试信息       │
│                                    │
│       ┌──────────────┐             │
│       │ 环境变量(N)... │  ← 点这个  │
│       └──────────────┘             │
│                    ┌──────┐        │
│                    │ 确定  │        │
│                    └──────┘        │
└────────────────────────────────────┘
```

点击右下角的 **「环境变量(N)...」** 按钮。

**③ 弹出「环境变量」窗口**

这个窗口分为上下两个框：

```
┌──────────────────────────────────────────┐
│  环境变量                                │
│                                          │
│  ┌─ XXX 的用户变量(U) ─────────────────┐ │
│  │                                     │ │
│  │  变量        值                      │ │
│  │  ─────────  ────────────────────     │ │
│  │  Path       C:\Users\xxx\...         │ │
│  │  TEMP       C:\Users\xxx\...         │ │
│  │  TMP        C:\Users\xxx\...         │ │
│  │                                     │ │
│  │         [新建(N)...] [编辑(E)...]     │ │
│  └─────────────────────────────────────┘ │
│                                          │
│  ┌─ 系统变量(S) ───────────────────────┐ │
│  │                                     │ │  ← 看这个框!
│  │  变量        值                      │ │
│  │  ─────────  ────────────────────     │ │
│  │  Path       C:\Windows\system32;...  │ │  ← 找到这一行!
│  │  ...                                │ │
│  │                                     │ │
│  │         [新建(N)...] [编辑(I)...]     │ │
│  └─────────────────────────────────────┘ │
│                                          │
│                     [确定]   [取消]       │
└──────────────────────────────────────────┘
```

**④ 关键操作：在下面的「系统变量」框里，找到 `Path` 那一行。**

用鼠标点击 `Path` 这一行，让它变成蓝色选中状态，然后点击下面的 **「编辑(I)...」** 按钮。

> ⚠️ 注意！是**下面那个框**（系统变量）里的 Path，不是上面那个框（用户变量）。

**⑤ 弹出「编辑环境变量」窗口**

```
┌────────────────────────────────────────┐
│  编辑环境变量                          │
│                                        │
│  变量名(N):                            │
│  ┌────────────────────────────────┐    │
│  │ Path                           │    │
│  └────────────────────────────────┘    │
│                                        │
│  变量值(V):                            │
│  ┌────────────────────────────────┐    │
│  │ C:\Windows\system32            │    │
│  │ C:\Windows                     │    │
│  │ C:\Windows\System32\Wbem       │    │
│  │ ...                            │    │
│  │                                │    │ ← 最下面有个空白行
│  └────────────────────────────────┘    │
│                                        │
│  [新建(N)] [编辑(E)] [删除(D)] [上移]   │
│                                        │
│                [确定]   [取消]          │
└────────────────────────────────────────┘
```

**⑥ 点击右边的「新建(N)」按钮。**

列表最下面会出现一个空白输入行：

```
│  │ C:\Windows\System32\Wbem       │    │
│  │                                │    │ ← 新出现的空白行，光标在这里闪
│  └────────────────────────────────┘    │
```

**⑦ 在空白行里输入 `C:\ffmpeg\bin`**

```
│  │ C:\Windows\System32\Wbem       │    │
│  │ C:\ffmpeg\bin                  │    │ ← 输入这个
│  └────────────────────────────────┘    │
```

> 💡 如果你之前复制了 `C:\ffmpeg\bin`，现在直接 Ctrl+V 粘贴就行。

**⑧ 一路点「确定」关掉所有窗口**

- 点这个窗口的「确定」
- 点"环境变量"窗口的「确定」
- 点"系统属性"窗口的「确定」

三个窗口全部关掉。

---

##### 第三部分：验证 ffmpeg 安装

**关掉当前的终端窗口，重新打开一个新的终端。**（必须重开！Windows 只有在打开新终端时才会读新的环境变量。）

在新终端里输入：

```bash
ffmpeg -version
```

你应该看到一大段输出，前几行类似这样：

```
ffmpeg version 7.0.2-essentials_build-www.gyan.dev Copyright (c) ...
built with gcc ...
configuration: ...
libavutil      59. ...
libavcodec     61. ...
libavformat    61. ...
```

🎉 **看到版本信息就说明 ffmpeg 安装成功了！**

> 如果还是报"不是内部或外部命令"，两个可能原因：
> 1. 路径输错了（比如 `C:\ffmpeg\bin` 写成了 `C:\ffmpeg`）→ 回到第④步重新检查
> 2. 关窗口那一步没做 → **关了终端再开一次**

---

#### 🍎 ffmpeg 安装教程 —— macOS 系统

最简单的方法是使用 Homebrew（Mac 上的软件包管理器）。打开「终端」App，输入：

```bash
brew install ffmpeg
```

等它跑完就装好了。输入 `ffmpeg -version` 验证。

> 如果你的 Mac 还没有装 Homebrew，先去 https://brew.sh 复制首页那条安装命令，在终端里跑一遍（大约需要 3～5 分钟），回来再执行 `brew install ffmpeg`。

---

#### 🐧 ffmpeg 安装教程 —— Linux 系统

**Ubuntu / Debian：**

```bash
sudo apt update
sudo apt install ffmpeg
```

**Fedora：**

```bash
sudo dnf install ffmpeg
```

**Arch：**

```bash
sudo pacman -S ffmpeg
```

装完后输入 `ffmpeg -version` 验证。

---

### 第三步：下载项目代码

现在把我们的项目文件弄到你的电脑上。**有两种方式，选一种就行：**

| 方式 | 适合谁 | 难度 |
|------|--------|------|
| 方式一：Git 命令下载 | 电脑上有 Git 的人 | ⭐ 简单 |
| **方式二：ZIP 下载**（推荐新手） | 没有 Git 的人 | ⭐ 最简单 |

---

#### ✅ 方式二：直接下载 ZIP（推荐！最简单）

> 📌 不需要装任何额外软件，用浏览器就能搞定。

**① 打开项目主页**

浏览器打开下面这个链接：

> 🔗 **项目地址：https://github.com/YanYuChunMing/bili-video-notes-workflow**

你会看到 GitHub 上这个项目的首页：

```
┌─────────────────────────────────────────────┐
│  YanYuChunMing / bili-video-notes-workflow  │
│                                             │
│  🎬 把 B站视频变成学习笔记 ...               │
│                                             │
│  ┌──────────┐                               │
│  │ ⭐ Star  │    ┌─────────────────────┐    │
│  └──────────┘    │  ⬇ Code  (绿色按钮) │    │
│                  └─────────────────────┘    │
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │  📄 README.md  (本文档的网页版)      │    │
│  │   ...                               │    │
│  └─────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
```

**② 点击绿色的「⬇ Code」按钮**

页面右上角有一个绿色的按钮，上面写着 "Code"。点击它，会弹出一个小菜单：

```
┌──────────────────────────┐
│  Clone                   │
│                          │
│  ○ HTTPS                 │
│  ○ SSH                   │
│                          │
│  https://github.com/...  │
│  ┌──────────────────┐    │
│  │ 📋 复制链接       │    │
│  └──────────────────┘    │
│                          │
│  ────────────────────    │
│  Download ZIP      ← 点  │
│                          │
└──────────────────────────┘
```

**③ 点击「Download ZIP」**

浏览器开始下载一个 zip 压缩包，文件名类似 `bili-video-notes-workflow-main.zip`，大约几百 KB。

**④ 解压到你喜欢的位置**

下载完成后，找到这个 zip 文件（在"下载"文件夹或浏览器底部下载栏）：

```
📁 下载
  └── bili-video-notes-workflow-main.zip   ← 找到它
```

**右键点击这个文件 → 选择「全部提取」或「解压全部」**：

```
┌──────────────────────────────────┐
│  提取压缩(Zipped)文件夹           │
│                                  │
│  文件将被提取到这个文件夹：        │
│  ┌────────────────────────────┐  │
│  │ D:\bili-video-notes-...    │  │ ← 改成你喜欢的
│  └────────────────────────────┘  │
│                        [浏览...]  │
│                                  │
│         [提取]                    │
└──────────────────────────────────┘
```

建议解压到 **D 盘根目录**（或者其他你容易找到的位置），比如 `D:\bili-video-notes-workflow`。然后点「提取」。

**⑤ 进入项目文件夹**

解压完成后，打开那个文件夹。你会看到里面有 `main.py`、`links.txt`、`README.md` 等文件。

> 🔗 **省事小窍门**：在文件夹顶部的路径栏（地址栏）里，直接输入 `powershell` 然后按回车，终端就会自动定位到这个文件夹！连 cd 命令都不用打。

```
┌──────────────────────────────────────────────────┐
│  📁  >  D:\bili-video-notes-workflow  [powershell]│ ← 地址栏里输入
│  ─────────────────────────────────────────────── │
│  文件    主页    共享    查看                      │
│  ─────────────────────────────────────────────── │
│                                                   │
│  📄 main.py    📄 links.txt    📄 README.md  ...  │
│  📁 src/       📁 ...                             │
│                                                   │
└──────────────────────────────────────────────────┘
```

---

#### 💻 方式一：用 Git 命令下载

> 适合已经装了 Git 的人。如果你不知道 Git 是什么，直接用上面的 ZIP 方式就行。

**如果你还没装 Git：** 去 `https://git-scm.com/download/win` 下载 Windows 版安装包，双击安装（一路点 Next 就行，不用改任何选项）。

装好后，在终端里执行：

```bash
git clone https://github.com/YanYuChunMing/bili-video-notes-workflow.git
```

下载完后进入项目文件夹：

```bash
cd bili-video-notes-workflow
```

---

### 第四步：创建虚拟环境并安装所有依赖

> 这一步会安装程序运行需要的全部"工具包"。包括 yt-dlp（负责下载 B站视频）、Whisper（负责语音转文字）、OpenCV（负责截图）等等。

确认你的终端当前在项目文件夹里（终端里显示的路径最后是 `bili-video-notes-workflow`）。

---

#### 4.1 创建虚拟环境

**什么是虚拟环境？** 就是给这个项目建一个"独立小房间"，里面装的各种工具包不会跟你电脑上其他程序搞混。以后如果不用了，把文件夹一删就干干净净。

在终端里执行：

```bash
python -m venv venv
```

（Mac 用户用 `python3 -m venv venv`）

这条命令会在项目文件夹里悄悄建一个叫 `venv` 的文件夹。屏幕上**不会有任何输出**，光标直接跳到下一行，这是正常的。

> 📁 你会在项目文件夹里看到一个新增的 `venv` 文件夹。**不要动它，也不要进去。**

---

#### 4.2 激活虚拟环境

| 你是 Windows？ | 你是 Mac / Linux？ |
|---------------|-------------------|
| `.\venv\Scripts\activate` | `source venv/bin/activate` |

激活成功后，终端最左边会多出一个 `(venv)` 标记：

```
(venv) D:\bili-video-notes-workflow>
```

看到 `(venv)` 就对了。

> ⚠️ **以后每次打开新终端要运行这个项目，都得先激活虚拟环境。** 退出用 `deactivate`。

---

#### 4.3 安装 Python 依赖包

确认终端左边有 `(venv)` 标记后，复制下面这条命令粘贴进去，按回车：

```bash
pip install -r requirements.txt
```

回车后，你会看到终端开始疯狂滚动：

```
Collecting faster-whisper>=1.0.0
  Downloading faster_whisper-1.1.1-py3-none-any.whl (x.x MB)
Collecting openai-whisper>=20231117
  Downloading openai_whisper-20240930-py3-none-any.whl (x.x MB)
Collecting openai>=1.0.0
  Downloading openai-1.68.0-py3-none-any.whl (x.x MB)
...
Installing collected packages: ...
Successfully installed ...
```

这个过程会持续 **2～5 分钟**（取决于网速），终端会刷刷刷地下各种包。等它停下来，光标重新出现，再执行下一条。

> 📦 这条命令装了哪些东西？Whisper 语音识别引擎、OpenAI 接口库、OpenCV 图像处理、OpenCC 繁简转换、TOML 配置解析器等等，一共 8 个核心依赖包。

---

#### 4.4 安装 yt-dlp（B站视频下载工具）

**yt-dlp 是独立安装的**，不在上面那个清单里。它是一个专门用来下载 B站、YouTube 等网站视频的命令行工具。

```bash
pip install yt-dlp
```

这个比较快，大约 10～20 秒就装好了。

> 🔗 yt-dlp 项目主页：https://github.com/yt-dlp/yt-dlp
>
> 你不需要去了解它怎么用，我们的程序会自动调用它。你只需要知道：**它是整个流水线的第一步——把 B站视频/音频扒下来。**

---

#### 4.5 确认安装成功

可以快速验证一下关键工具都装好了：

```bash
yt-dlp --version
```

如果显示类似 `2025.01.15` 这样的版本号，说明 yt-dlp 装好了。

```bash
pip list
```

这条命令会列出虚拟环境里安装的所有包。你可以在输出里找找有没有 `faster-whisper`、`openai`、`opencv-python`、`yt-dlp` 这几个——有的话就万事大吉。

---

### 第五步：创建配置文件

在终端里执行：

```bash
copy config.example.toml config.toml
```

> 这条命令的意思是"复制模板文件，生成一份你自己的配置文件"。运行后项目文件夹里会多一个 `config.toml`。

**这个文件暂时不用改**，默认配置已经可以直接用了。以后想调优（比如换更大的 Whisper 模型让识别更准）再打开改。

---

**🎉 到此为止，环境就全部搭好了！** 接下来只需要搞定 API 密钥就能开始用了。

---

## 🔑 DeepSeek 账号注册与 API 密钥获取

> 💡 在这部分，我会一步一步陪你注册 DeepSeek 账号并获取 API 密钥。
>
> 整个过程大约 **3～5 分钟**，而且 **DeepSeek 现在注册就有免费额度**，不花钱也能用很久。

---

### 为什么要注册 DeepSeek？

我们的程序的"智能"来自 DeepSeek —— 它是一个国产大语言模型，跟 ChatGPT 是同一类东西。程序调用它的接口来完成三件事：

| 功能 | 说明 |
|------|------|
| 加标点 + 分段 | 语音转出来的文字没有标点、没有分段，AI 帮你加上 |
| 写学习笔记 | AI 读完整个视频的文字版，提炼出核心知识点 |
| 画思维导图 | AI 把知识点整理成层级结构，做成可浏览的导图 |

**💰 要花钱吗？** DeepSeek 按使用量收费，但非常非常便宜——处理一小时视频的文字大概花 **几分钱**。

**🎁 新用户福利：** 注册就送 **10 元免费额度**（新用户通常都有），给你白嫖几十个小时视频的处理量。

**🔋 用完了怎么充？** 在后台左侧菜单点「充值」，最低充 **1 元起步**，几块钱就能用很久。

> 📌 你需要用到的 DeepSeek 链接汇总：
>
> | 用途 | 链接 |
> |------|------|
> | 注册 / 登录后台 | https://platform.deepseek.com/ |
> | API 文档（遇到问题查） | https://platform.deepseek.com/api-docs/ |
> | 充值 / 查看余额 | 登录后左侧菜单 → 「用量」或「充值」 |

---

### Step 1：打开 DeepSeek 官网并注册账号

**① 打开浏览器，地址栏输入 `platform.deepseek.com`，回车。**

你应该看到一个深蓝色主题的页面，顶部有"DeepSeek"的 Logo。

**② 点击页面右上角的「登录」按钮。**

页面跳转到登录界面，你会看到两个选项：手机号登录 / 邮箱登录。

**③ 如果你是第一次来，点击「注册」或「没有账号？去注册」。**

注册页面会让你选择注册方式：

| 注册方式 | 怎么做 |
|----------|--------|
| 手机号 | 输入手机号 → 点"获取验证码" → 输入收到的 6 位数字 → 设置密码 |
| 邮箱 | 输入邮箱地址 → 点"获取验证码" → 去邮箱里找到验证码 → 回来输入 → 设置密码 |

> 📱 推荐用手机号，最简单。国内手机号直接输入就行。

**④ 填写完信息后，点「注册」。**

看到"注册成功"或自动跳转到后台页面，说明账号创建完毕。

> 如果你在注册页面看到的是英文界面，页面右上角或底部一般有语言切换选项，选"中文"就行。

---

### Step 2：登录并进入 API 管理后台

注册完成后，你应该会自动登录进入后台。如果没有，重新打开 `platform.deepseek.com` 登录。

登录后你会看到一个后台管理界面。页面布局大概是这样的：

```
┌──────────────────────────────────────────────┐
│  DeepSeek  Logo          🔔 消息   👤 头像    │
├──────────┬───────────────────────────────────┤
│          │                                    │
│  概览    │      欢迎使用 DeepSeek API          │
│  API Keys│      账户余额: ¥10.00              │
│  用量    │      已用: ¥0.00                   │
│  账单    │       ...                          │
│  设置    │                                    │
│          │                                    │
└──────────┴───────────────────────────────────┘
```

> 🔍 **找什么？** 看左边的菜单栏。我们的目标是 **「API Keys」**。

---

### Step 3：创建 API Key（密钥）

> "API Key" 就是一把钥匙。有了它，程序才能"敲开"DeepSeek 的大门，请它帮忙处理文字。

**① 点击左侧菜单里的「API Keys」。**

页面切换到 API 密钥管理界面。如果你是新账号，这里是空的，还没有任何密钥。

**② 点击「创建 API Key」按钮（通常在右上角，蓝色或绿色的按钮）。**

弹出一个创建窗口 / 对话框：

```
┌─────────────────────────────────┐
│  创建 API Key                    │
│                                  │
│  名称: [________________]        │
│        （随便填，比如 bili笔记）  │
│                                  │
│  过期时间: ○ 永不过期  ○ 30天    │
│                                │
│        [取消]    [确定创建]      │
└─────────────────────────────────┘
```

**③ 在"名称"框里随便填一个你能记住的名字，比如 `bili笔记`。过期时间选「永不过期」。**

**④ 点击「确定创建」。**

弹出一个结果窗口，**这是你唯一能看到完整密钥的机会**：

```
┌─────────────────────────────────────────────┐
│  ⚠️ 请立即复制保存，关闭后将无法再次查看     │
│                                              │
│  sk-a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8   │
│                                  [📋 复制]   │
│                                              │
│                         [我已知晓，关闭]      │
└─────────────────────────────────────────────┘
```

**⑤ 立刻点击那个 📋 复制按钮，把密钥复制下来。**

密钥是一长串以 `sk-` 开头的字符，大概 30～40 个字符长。复制后**不要关掉这个窗口**，先去完成下一步。

> ⚠️ **重要！这个密钥只显示这一次。关掉之后就再也看不到完整的了。** 如果你忘了复制就关掉了，没关系，回到 API Keys 页面删掉这个重新创建一个就行（免费，不限次数）。

**⑥ 复制完成后，点击「我已知晓，关闭」。**

回到 API Keys 页面，你应该看到你刚创建的密钥出现在列表里，但中间部分被 `****` 隐藏了。这是正常的，说明密钥已安全存储。

---

### Step 4：把密钥写入项目配置文件

> 现在你手里握着 API 密钥（一串 `sk-` 开头的东西），要把它告诉我们的程序。

**① 在项目文件夹里，复制密钥模板文件：**

回到终端（确认在项目文件夹里），输入：

```bash
copy .env.example .env
```

这条命令做了什么？项目里有一个 `.env.example` 模板文件，你刚才把它复制了一份，新文件叫 `.env`。程序会读取 `.env` 里的密钥。

**② 用记事本打开 `.env` 文件：**

在项目文件夹里找到 `.env` 这个文件。注意：这个文件没有名字，只有后缀 `.env`。**双击它，选择用"记事本"打开。**

> 如果双击没反应，右键 → "打开方式" → 选择"记事本"。

打开后你会看到两行文字：

```
DEEPSEEK_API_KEY=sk-your-api-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

**③ 把第一行 `sk-your-api-key-here` 替换成你刚才复制的真实密钥：**

```
DEEPSEEK_API_KEY=sk-a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

> 💡 把原来 `sk-your-api-key-here` 这几个单词删掉，然后把复制的真实密钥粘贴进去。**不要多出空格，不要换行。**

**④ 保存文件（Ctrl+S），关掉记事本。**

完成！

---

### 没有 API Key 能用吗？

**能用。** 程序会自动检测你有没有配密钥：

- **配了密钥** → AI 功能全部开启：标点补全 ✅、学习笔记 ✅、思维导图 ✅
- **没配密钥** → AI 功能自动跳过，只做语音转文字。你还是能得到：
  - 📝 纯文字稿（能用）
  - 📝 带时间戳文字稿（能用）
  - ⏭️ 标点稿（跳过，输出原文）
  - ⏭️ 学习笔记（跳过）
  - ⏭️ 思维导图（跳过）

所以建议还是花 3 分钟注册一下。不花钱，体验好很多。

---

## ▶️ 运行你的第一个视频

环境搭好了，密钥配好了，来跑第一个视频吧！

---

### 添加 B站链接

用记事本打开项目文件夹里的 `links.txt`。

把你要处理的 B站视频链接**每行一个**粘贴进去：

```
https://www.bilibili.com/video/BV1eRrABqE7P
```

> 💡 支持三种格式：
> - 标准链接：`https://www.bilibili.com/video/BVxxxxxxxx`
> - 短链接：`https://b23.tv/xxxxxx`
> - 番剧链接：`https://www.bilibili.com/bangumi/play/epxxxxxx`
>
> 链接里带 `?vd_source=xxx` 这种尾巴参数也没关系，程序会自动处理。
>
> 以 `#` 开头的行为注释行，会被跳过。

保存文件，关掉记事本。

---

### 启动程序

回到终端，确认左边有 `(venv)` 标记（没有的话先执行 `.\venv\Scripts\activate`），然后输入：

```bash
python main.py --task basic_test
```

按回车。程序开始跑了！🎉

---

### 看懂运行日志

程序运行过程中，终端会不断输出日志。下面是你应该看到的正常流程：

```
=== 启动任务: basic_test ===
模式: basic
链接文件: links.txt
[1] ===== 开始处理: https://www.bilibili.com/video/BV1eRrABqE7P =====
  ↓ 正在下载音频（yt-dlp）...
  ↓ 正在语音转录（Whisper） ← 这一步最慢，耐心等待
  ↓ AI 正在添加标点...
  ↓ AI 正在生成笔记摘要...
  ↓ AI 正在生成思维导图...
[1] ===== 处理完成: 从混乱到清晰：5分钟掌握Go模块 =====
=== 任务完成: basic_test ===
总计 1 个链接 | 成功 1 | 失败 0 | 跳过 0
```

**每行日志是什么意思：**

| 日志内容 | 程序在干什么 | 你需要做什么 |
|----------|-------------|-------------|
| `启动任务: basic_test` | 读取配置，准备开始 | 不用管 |
| `开始处理: ...` | 正在处理你添加的那个链接 | 不用管 |
| `下载音频（yt-dlp）` | 正在从 B站下载视频的音频部分 | 等 |
| `语音转录（Whisper）` | 把音频转成文字。**这是最慢的一步** | 耐心等，可以去倒杯水 ☕ |
| `AI 正在添加标点` | 调用 DeepSeek 给文字加标点分段 | 等 |
| `AI 正在生成笔记摘要` | 调用 DeepSeek 提炼知识要点 | 等 |
| `AI 正在生成思维导图` | 调用 DeepSeek 画知识结构图 | 等 |
| `处理完成: xxx` | 这一个视频处理完毕 | 🎉 |
| `任务完成` | 所有链接都处理完了 | 去看成果！ |

> 🟢 每行日志前面有绿色的 `INFO` 字样是正常的。如果看到红色的 `ERROR`，说明出错了，去看 [常见问题排查](#-常见问题排查)。

---

### 要多久？

| 环节 | 耗时 | 说明 |
|------|------|------|
| 下载音频 | 2～5 分钟 | 取决于网速 |
| 语音转录 | 2～20 分钟 | **有显卡快，没显卡慢** |
| AI 处理 | 不到 1 分钟 | 三步加起来约 30～60 秒 |

> 🖥️ 如果你的电脑有 NVIDIA 独立显卡，程序自动用 GPU 加速，20 分钟的视频大概 2～3 分钟转录完。
>
> 💻 如果是普通笔记本没有独显，纯 CPU 跑，同样 20 分钟的视频大概 10～20 分钟转录完。**慢，但能用。**

---

## 📁 查看成果

程序跑完后，打开项目文件夹，进入 `outputs` 文件夹。你会看到：

```
outputs/
└── 001_从混乱到清晰：5分钟掌握Go模块/
    ├── audio.wav               ← 下载的音频文件（不需要管）
    ├── segments.json           ← 内部数据（不需要管）
    ├── metadata.json           ← 视频信息（标题/UP主/时长）
    │
    └── results/                ← ⭐ 你的笔记都在这里！
        ├── transcript.txt           ← ① 纯文字稿
        ├── transcript_with_timestamps.md  ← ② 带 [MM:SS] 时间戳的
        ├── transcript_with_punct.txt      ← ③ AI 加了标点的文字稿
        ├── summary.md               ← ④ 学习笔记 ⭐ 重点看
        ├── mindmap.md               ← ⑤ 思维导图 Markdown 版
        └── mindmap.html             ← ⑥ 思维导图 ⭐ 双击用浏览器打开
```

**建议先看这两个：**
1. 打开 `summary.md` → 花 3 分钟看完 AI 提炼的知识要点
2. 双击 `mindmap.html` → 在浏览器里看思维导图，知识结构一目了然

> 💡 你可以在 `links.txt` 里放多个链接，程序会一个一个处理。每处理完一个，继续下一个，跑完的会自动跳过，不会重复处理。

---

## 🎮 运行模式说明

### Basic 模式（推荐日常使用）

只下载音频 → 语音转文字 → AI 笔记生成。速度快，适合网课、知识视频、会议录音。

```bash
python main.py --task basic_test
```

### With-Images 模式（适合教程类视频）

下载完整视频 → 除基本产物外，还会截取关键画面并嵌入到笔记中，生成图文并茂的笔记。

```bash
python main.py --task with_images_test
```

### 不依赖配置文件运行

```bash
python main.py --input links.txt --mode basic
```

---

## 📂 项目文件结构

```
bili-video-notes-workflow/          📁 项目根目录
│
├── main.py                         🚪 程序入口
├── requirements.txt                📦 依赖清单
├── config.example.toml             📋 配置模板
├── config.toml                     📋 你的配置
├── .env.example                    🔑 密钥模板
├── .env                            🔑 你的密钥
├── links.txt                       ✏️ 视频链接
├── links_with_images.txt           ✏️ 截图模式链接
│
├── Dockerfile                       🐳 Docker 镜像 (CPU)
├── Dockerfile.gpu                   🐳 Docker 镜像 (NVIDIA GPU)
├── docker-compose.yml               🐳 Docker 编排 (CPU / GPU 双 profile)
├── .dockerignore                    🐳 Docker 忽略规则
├── docker_install.sh                🐳 Linux/Mac 一键装 Docker
├── docker_install.ps1               🐳 Windows 一键装 Docker
│
├── README.md                         📖 本文档
├── CHANGELOG.md                     📝 版本日志
├── CONTRIBUTING.md                 🤝 贡献指南
├── PROJECT_FRAMEWORK.md            🏗️ 框架文档
│
├── src/                            💻 源码
│   ├── downloader.py               #   音视频下载
│   ├── transcriber.py              #   语音转文字
│   ├── text_cleaner.py             #   AI 标点补全
│   ├── summarizer.py               #   AI 摘要
│   ├── mindmap.py                  #   AI 思维导图
│   ├── screenshotter.py            #   智能截图
│   ├── markdown_builder.py         #   图文笔记
│   ├── video_splitter.py           #   视频分段
│   ├── link_parser.py              #   链接解析
│   ├── config_loader.py            #   配置加载
│   └── utils.py                    #   工具箱
│
├── outputs/                        🎯 产物输出
├── downloads/                      📥 下载缓存
├── logs/                           📜 运行日志
├── processed.json                  ✅ 已处理记录
└── failed.json                     ❌ 失败记录
```

---

## ❓ 常见问题排查

### Q1：`'python' 不是内部或外部命令`

**原因**：Python 没装，或者装了但没勾 `Add Python to PATH`。

**解决**：回到 [第一步](#第一步检查--安装-python) 重新安装，**一定**勾选 Add Python to PATH。装完后**关掉终端重新打开**。

---

### Q2：`No module named 'xxx'`

**原因**：依赖包没装全，或虚拟环境没激活（终端左边没有 `(venv)`）。

**解决**：
```bash
.\venv\Scripts\activate
pip install -r requirements.txt
pip install yt-dlp
```

---

### Q3：`'yt-dlp' 不是内部或外部命令`

**原因**：yt-dlp 需要单独安装，不在 requirements.txt 里。

**解决**：
```bash
pip install yt-dlp
```

---

### Q4：下载失败 `unable to download webpage`

**原因**：短时间内下载太多，B站暂时限制了你的 IP。

**解决**：等 10～30 分钟后再试；或者用手机热点切换 IP。

---

### Q5：下载很慢

**原因**：B站对非登录用户限速。

**解决**：正常现象。1 小时视频的音频大约 50～100MB。

---

### Q6：转录时内存溢出 / CUDA 报错

**原因**：显卡显存不够。

**解决（二选一）：**
- 用记事本打开 `config.toml`，把 `whisper.model` 改成 `"small"` 或 `"base"`
- 把 `whisper.device` 改成 `"cpu"`（慢但稳定）

---

### Q7：DeepSeek API 调用失败

**原因**：密钥不对 / 没余额了 / 网络不通。

**检查：**
1. 用记事本打开 `.env`，确认 `DEEPSEEK_API_KEY` 后面是一串真实的 `sk-` 开头的密钥，不是 `sk-your-api-key-here`
2. 浏览器打开 `platform.deepseek.com`，登录后看看余额
3. 如果余额为 0，可以充值（很便宜，几块钱能用很久）

---

### Q8：`'ffmpeg' 不是内部或外部命令`

**原因**：ffmpeg 没装，或 bin 目录没加到 PATH。

**解决**：参考 [第二步](#第二步检查--安装-ffmpeg)。

---

### Q9：截图不生效

需满足：① 用 `with_images` 模式 ② 已安装 opencv 和 scikit-image（requirements.txt 已含）。

---

### Q10：同一个视频每次都重新处理

`processed.json` 文件丢了。程序会自动创建，不用管它。

---

### Q11：跑一半断了，怎么继续？

直接重新跑。程序自动跳过处理过的，从断点继续。想强刷某个视频，删掉 `processed.json` 里对应那条。

---

## ⚙️ 配置说明（进阶）

> 📌 默认就能用，下面供想调优的用户参考。

```toml
[whisper]
model = "medium"          # tiny/base/small/medium/large（越大越准越吃显存）
language = "Chinese"
device = "cuda"           # cuda（NVIDIA）或 cpu

[deepseek]
model = "deepseek-chat"
base_url = "https://api.deepseek.com"

[screenshot]
enabled = false

[[tasks]]
name = "basic_test"
input_file = "links.txt"
mode = "basic"
```

---

## 📊 技术栈

| 环节 | 技术 |
|------|------|
| 语言 | Python 3.10+ |
| 下载 | yt-dlp |
| 音频 | ffmpeg |
| 转录 | faster-whisper / openai-whisper |
| AI | DeepSeek API |
| 繁简 | OpenCC |
| 截图 | OpenCV + scikit-image (SSIM) |

---

## ⚠️ 已知限制

| 限制 | 说明 |
|------|------|
| Basic 不下载视频 | 纯音频 |
| 登录视频 | 目前不支持 Cookie |
| ffmpeg | 需手动安装 |
| AI 可选 | 不配密钥只做转录 |
| yt-dlp | 需额外 `pip install yt-dlp` |

---

## 📚 更多文档

| 文档 | 内容 |
|------|------|
| [PROJECT_FRAMEWORK.md](PROJECT_FRAMEWORK.md) | 开发文档：架构、接口、流程 |
| [CHANGELOG.md](CHANGELOG.md) | 版本更新日志 |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 贡献指南 |

---

## 📄 License

MIT License
