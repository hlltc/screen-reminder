# Screen Reminder

> 一个不打断你编码的桌面健康管家，默默守护你的眼睛、颈椎、腰椎。

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![PySide6](https://img.shields.io/badge/GUI-PySide6-green.svg)](https://doc.qt.io/qtforpython-6/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()

Screen Reminder 是一款面向程序员的跨平台桌面健康提醒工具，通过**全屏遮罩倒计时 + 智能调度**，在不打断编码心流的前提下帮助你建立健康的屏幕使用习惯。

## ✨ 功能特性

| 模块 | 触发间隔 | 提醒方式 |
|------|----------|----------|
| 👁 **护眼** | 默认 20 min（可配 5–60 min） | 全屏遮罩倒计时 20 s |
| 🚶 **久坐** | 默认 55 min（可配 20–120 min） | 全屏遮罩倒计时 3 min |
| 💧 **补水** | 默认 45 min（可配 15–120 min） | 半屏弹窗卡片（喝了/跳过） |
| 🧠 **智能调度** | 工作时段感知、空闲检测、暂停 | 09:00–18:00 Mon–Fri |

三个提醒均直接弹出遮罩，无桌面通知打扰。按 `Esc` 跳过。

## 🖥️ 界面

```
左键点击托盘 → 弹出小组件              右键点击托盘 → 菜单
┌──────────────────────────────┐     ┌──────────────────┐
│  ●  Screen Reminder          │     │ ⏸ 暂停 30 分钟   │
├──────────────────────────────┤     │ ⏸ 暂停 1 小时    │
│  👁 下次护眼：18 分 32 秒     │     │ ⏸ 暂停到明天      │
│  🚶 下次站立：53 分 12 秒     │     ├──────────────────┤
│  💧 饮水：400 / 2000ml (20%) │     │ 💧 记录喝水       │
├──────────────────────────────┤     │ ⚙ 设置            │
│  ⏸ 暂停30min  ⏸ 暂停1h      │     ├──────────────────┤
│  ⏸ 暂停2h     💧 喝了100ml   │     │ ❌ 退出程序        │
│  💧 喝了200ml 💧 喝了300ml   │     └──────────────────┘
└──────────────────────────────┘
```

## 📦 安装

### 源码运行

```bash
git clone git@github.com:hlltc/screen-reminder.git
cd screen-reminder
uv sync
uv run python -m src
```

### 快速预览 (Demo)

```bash
uv run python -m src --demo
# +8s 护眼遮罩 → +16s 喝水弹窗 → +24s 久坐遮罩
```

### 打包

```bash
uv run python build.py
# 输出: dist/ScreenReminder.exe    (Windows)
#       dist/ScreenReminder         (macOS/Linux)
```

## ⚙️ 设置

右键托盘图标 → **⚙ 设置**，四个标签页即时生效：

- **通用**：工作时段、午休、空闲检测阈值
- **护眼**：提醒间隔 (5–60 min)、休息时长 (10–120 s)、遮罩透明度
- **久坐**：提醒间隔 (20–120 min)、站立时长 (30–600 s)
- **补水**：提醒间隔 (15–120 min)、单次/每日水量

## 🏗️ 技术栈

| 技术 | 用途 |
|------|------|
| **Python 3.11+** | 核心语言 |
| **PySide6 (Qt)** | 跨平台 GUI + 系统托盘 |
| **pynput** | 键盘/鼠标空闲检测 |
| **SQLAlchemy + SQLite** | 本地数据持久化 |
| **pydantic-settings** | 配置管理 |
| **loguru** | 日志 |
| **Pillow** | 图标处理 |
| **uv** | 虚拟环境 & 依赖管理 |
| **PyInstaller** | 打包分发 |

## 📁 项目结构

```
screen-reminder/
├── src/
│   ├── main.py              # 入口
│   ├── app/                 # 应用生命周期、单例控制
│   ├── tray/                # 系统托盘 + 弹出小组件
│   ├── ui/                  # 设置窗口、全屏遮罩、喝水弹窗
│   ├── modules/             # 健康模块（护眼/久坐/补水）
│   ├── engine/              # 调度引擎、空闲检测
│   ├── data/                # 数据库模型 & 访问层
│   └── utils/               # 配置、常量、资源路径
├── assets/icons/            # 应用图标
├── build.py                 # 打包脚本
├── pyproject.toml           # 项目元数据 & 依赖
└── doc/PRD.md               # 产品需求文档
```

## 📝 路线图

- [x] Phase 1 — MVP：护眼 + 久坐 + 补水 + 托盘小组件 + 设置 + Demo 模式
- [ ] Phase 2 — 体验：APM 工作强度感知、Lottie 拉伸动画、数据面板
- [ ] Phase 3 — 智能：摄像头姿态检测、日历联动、PDF 健康报告
- [ ] Phase 4 — 生态：移动端 App、手表联动、浏览器扩展

## 📄 协议

MIT License
