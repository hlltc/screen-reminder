# Screen Reminder

> 一个不打断你编码的桌面健康管家，默默守护你的眼睛、颈椎、腰椎。

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![PySide6](https://img.shields.io/badge/GUI-PySide6-green.svg)](https://doc.qt.io/qtforpython-6/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)]()

Screen Reminder 是一款面向程序员的跨平台桌面健康提醒工具，通过**智能调度 + 渐进式提醒 + 游戏化激励**，在不打断编码心流的前提下帮助你建立健康的屏幕使用习惯。

## ✨ 功能特性

| 模块 | 功能 | 默认配置 |
|------|------|----------|
| 👁 **护眼** | 20-20-20 法则（每 20 分钟看远处 20 秒） | 20 min / 20 s |
| 🚶 **久坐** | 定时站立提醒 + 全屏倒计时锁定 | 55 min / 3 min |
| 💧 **补水** | 定时喝水提醒 + 一键记录饮水量 | 45 min / 每日 2000ml |
| 🧠 **智能调度** | 工作时段感知、空闲检测、暂停/恢复 | 09:00–18:00 Mon–Fri |

**渐进式提醒**：托盘变色 → 桌面通知 → 半透明遮罩 → 全屏倒计时，给足选择余地。

## 🖥️ 界面预览

```
左键点击托盘 → 弹出健康小组件             右键点击托盘 → 功能菜单
┌──────────────────────────────┐     ┌──────────────────┐
│  ●  Screen Reminder          │     │ ⏸ 暂停 30 分钟   │
├──────────────────────────────┤     │ ⏸ 暂停 1 小时    │
│  👁 下次护眼：18 分 32 秒     │     │ ⏸ 暂停到明天      │
│  🚶 下次站立：53 分 12 秒     │     ├──────────────────┤
│  💧 饮水：400 / 2000ml (20%) │     │ 💧 记录喝水       │
├──────────────────────────────┤     │ ⚙ 设置            │
│  ⏸ 暂停30min  ⏸ 暂停1h      │     ├──────────────────┤
│  💧 50ml  💧 100ml           │     │ ❌ 退出程序        │
│  💧 200ml 💧 300ml           │     └──────────────────┘
└──────────────────────────────┘
```

## 📦 安装

### 方式一：源码运行（开发者）

```bash
git clone git@github.com:hlltc/screen-reminder.git
cd screen-reminder

# 使用 uv 管理虚拟环境和依赖
uv sync
uv run python -m src
```

### 方式二：打包可执行程序

```bash
# 添加打包依赖
uv add --dev pyinstaller

# 构建
uv run python build.py

# 输出在 dist/ 目录下
#   Windows: dist/ScreenReminder.exe
#   macOS:   dist/ScreenReminder
#   Linux:   dist/ScreenReminder
```

## ⚙️ 设置

右键托盘图标 → **⚙ 设置**，可自定义：

- **通用**：工作时段、午休、空闲检测阈值
- **护眼**：提醒间隔 (5–60 min)、休息时长 (10–120 s)、遮罩透明度
- **久坐**：提醒间隔 (20–120 min)、锁定时长 (30–600 s)
- **补水**：提醒间隔 (15–120 min)、单次/每日水量

设置保存后**即时生效**，无需重启。

## 🏗️ 技术栈

| 技术 | 用途 |
|------|------|
| **Python 3.11+** | 核心语言 |
| **PySide6 (Qt)** | 跨平台 GUI + 系统托盘 |
| **pynput** | 键盘/鼠标空闲检测 |
| **plyer** | 跨平台桌面通知 |
| **SQLAlchemy + SQLite** | 本地数据持久化 |
| **pydantic-settings** | 配置管理 |
| **uv** | 虚拟环境 & 依赖管理 |
| **PyInstaller** | 打包分发 |

## 📁 项目结构

```
screen-reminder/
├── src/
│   ├── main.py              # 入口
│   ├── app/                 # 应用生命周期、单例控制
│   ├── tray/                # 系统托盘 + 弹出小组件
│   ├── ui/                  # 设置窗口、休息遮罩
│   ├── modules/             # 健康模块（护眼/久坐/补水）
│   ├── engine/              # 调度引擎、空闲检测、通知
│   ├── data/                # 数据库模型 & 访问层
│   ├── platform/            # 跨平台 API 封装（预留）
│   └── utils/               # 配置管理、常量
├── assets/                  # 图标 & 动画资源
├── build.py                 # 打包脚本
├── pyproject.toml           # 项目元数据 & 依赖
└── doc/PRD.md               # 产品需求文档
```

## 🤝 开发

```bash
uv sync --all-extras          # 安装含开发依赖
uv run pytest                 # 运行测试（待补充）
uv run ruff check src/        # 代码检查
```

## 📝 路线图

- [x] Phase 1 — MVP：护眼 + 久坐 + 补水 + 托盘小组件 + 设置
- [ ] Phase 2 — 体验：APM 工作强度感知、Lottie 拉伸动画、数据面板
- [ ] Phase 3 — 智能：摄像头姿态检测、日历联动、PDF 健康报告
- [ ] Phase 4 — 生态：移动端 App、手表联动、浏览器扩展

## 📄 协议

MIT License
