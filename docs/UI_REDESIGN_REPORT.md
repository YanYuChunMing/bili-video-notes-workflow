# 烟雨春明前端重构实现方案

## 设计稿

品牌标识：新界面以“烟雨春明”为主品牌，Logo 使用“春”字图形章，结合花瓣、金色光点和绿色渐变，形成与参考图 `docs/learning_screenshot_strategy/TCX.jpg` 一致的春日、轻盈、明亮识别系统。

色彩方案：

| 用途 | 色值 | 说明 |
| --- | --- | --- |
| 春绿主色 | `#7acb5a` | 对应参考图中的发饰与叶片 |
| 深绿文字 | `#183327` | 保证白天模式可读性 |
| 金色高光 | `#d9a846` | 对应发丝与暖光 |
| 珊瑚强调 | `#ff6c45` | 对应参考图红色花饰 |
| 白天背景 | `#f8fff2` + 绿金径向光 | 清透、明亮、柔和 |
| 夜晚背景 | `#071813` + 墨绿渐变 | 保留春绿识别色，降低亮度 |

核心组件：

| 组件 | 实现位置 | 设计说明 |
| --- | --- | --- |
| 点击按钮 | `app/ui.py` 全局 CSS `.stButton > button` | 胶囊按钮、绿金渐变、悬浮上移动效 |
| 列表组件 | `.ym-list`、`.ym-list-item` | 三列扫描布局，点状状态标识与右侧标签 |
| 输入框 | Streamlit `text_area/selectbox` 全局样式 | 半透明白底、圆角、浅绿描边 |
| 昼夜切换 | `render_theme_controller()` | Session state 驱动，点击后重绘昼夜主题 |
| 文件夹组件 | `.ym-folder-grid`、`.ym-folder` | 纸夹标签造型，绿金渐变 |
| 加载条 | `.ym-loader` | 渐变条横向循环动画 |
| Logo/图形展示 | `.ym-brand`、`.ym-mark`、`.ym-hero` | 品牌章 + 参考图融合背景 |

布局草图：

```text
┌──────────────────────────────────────────────┐
│ Logo 烟雨春明                         昼夜切换 │
├──────────────────────────────────────────────┤
│ Hero: 烟雨春明 + TCX 视觉背景 + 超级模式视觉按钮 │
├──────────────────────────────────────────────┤
│ 成功处理 │ 失败数 │ 输出目录 │ Whisper 模型     │
├──────────────────────────────────────────────┤
│ 统一工作台：一键打开超级模式                   │
│ 左：链接输入 / 文件加载  右：模型、语言、截图参数 │
├───────────────────────┬──────────────────────┤
│ 系统状态列表           │ 最近处理列表           │
├───────────────────────┴──────────────────────┤
│ 文件夹组件：最近输出目录                       │
└──────────────────────────────────────────────┘
```

## 代码实现

主要改动：

- 新增 `app/ui.py`，集中管理全新 UI、样式、主题、统一工作台和运行流程。
- 重写 `streamlit_app.py`，主页直接进入“烟雨春明”新界面。
- 重写 `pages/01_基础功能.py` 与 `pages/02_带图功能.py`，两个旧入口都进入同一工作台；带图入口默认打开超级模式。
- 保留后端 `PipelineRunner` 行为，基础模式仍传入 `mode="basic"`，超级模式传入 `mode="with_images"`。
- 使用本地 `TCX.jpg` 生成 base64 data URI，避免部署时静态路径失效。

关键交互：

- “一键打开超级模式”按钮通过 `st.session_state["ym_super_mode"]` 在基础模式与带图模式之间切换。
- 昼夜切换通过 `st.session_state["ym_theme"]` 控制 CSS 重绘。
- 输入方式会随模式自动切换默认文件：基础模式使用 `links.txt`，超级模式使用 `links_with_images.txt`。
- 超级模式展开截图开关、最小截图间隔、相似度去重阈值。

## 测试报告

已执行：

```powershell
python -m py_compile streamlit_app.py app\ui.py pages\01_基础功能.py pages\02_带图功能.py
python -c "from streamlit.testing.v1 import AppTest; at=AppTest.from_file('streamlit_app.py', default_timeout=20); at.run(); print(len(at.exception))"
python -c "from streamlit.testing.v1 import AppTest; at=AppTest.from_file('streamlit_app.py', default_timeout=20); at.run(); at.button[1].click().run(); print([b.label for b in at.button[:3]]); print([c.label for c in at.checkbox]); at.button[0].click().run(); print([b.label for b in at.button[:2]])"
```

结果：

- Python 编译通过，新增与改写的前端文件无语法错误。
- Streamlit AppTest 首页运行无异常。
- 超级模式切换后按钮从“开始生成文字笔记”切换为“开始生成图文笔记”，并出现“启用智能截图”参数。
- 昼夜切换后按钮文案从“切换到夜晚模式”切换为“切换到白天模式”。
- 本地临时启动 Streamlit 后，`http://127.0.0.1:8501` 返回 HTTP 200。

建议人工验收：

1. 运行 `streamlit run streamlit_app.py`，确认首页视觉完全替换旧设计。
2. 点击昼夜切换，确认背景、卡片和文字进入夜晚模式，再次点击恢复白天模式。
3. 点击“一键打开超级模式”，确认截图参数平滑出现，按钮文案切换。
4. 粘贴 B站链接，确认链接识别数量正确。
5. 分别在基础模式和超级模式启动一次短视频任务，确认 `PipelineRunner` 分别收到 `basic` 与 `with_images` 模式。
6. 在窄屏浏览器宽度下检查 Hero、统计卡、列表和文件夹组件是否单列展示且无重叠。
