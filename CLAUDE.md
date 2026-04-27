# Houdini AI Assistant - 项目规划

## 项目概述

一个运行在 Houdini 内部的 AI Agent 插件，用户通过自然语言对话控制 Houdini。
Agent 可以查询场景状态、创建/删除/连接节点、修改参数、生成 VEX/Python 代码，
执行所有 HOM API 支持的操作。支持多 AI 后端和本地模型，数据可完全离线。

## 核心架构

```
┌──────────────────────────────────────────────────────────┐
│                        Houdini                           │
│                                                          │
│  ┌──────────────────┐    ┌───────────────────────────┐  │
│  │    UI Layer       │    │    Core Agent Engine       │  │
│  │                   │    │                           │  │
│  │ ┌───────────────┐ │    │  ┌─────────────────────┐  │  │
│  │ │ Splash Screen │ │    │  │  Provider Manager   │  │  │
│  │ │  (启动面板)    │ │    │  │  - Claude           │  │  │
│  │ └───────────────┘ │    │  │  - OpenAI (GPT)     │  │  │
│  │ ┌───────────────┐ │◄──►│  │  - DeepSeek         │  │  │
│  │ │  Chat Panel   │ │    │  │  - Gemini           │  │  │
│  │ │  (主聊天面板)  │ │    │  │  - Ollama (本地)    │  │  │
│  │ └───────────────┘ │    │  │  - LM Studio (本地) │  │  │
│  │ ┌───────────────┐ │    │  └─────────────────────┘  │  │
│  │ │ Settings Panel│ │    │  ┌─────────────────────┐  │  │
│  │ │  (设置面板)    │ │    │  │  Tool Layer (HOM)   │  │  │
│  │ └───────────────┘ │    │  │  - Node CRUD         │  │  │
│  │                   │    │  │  - Param R/W         │  │  │
│  └──────────────────┘    │  │  - Selection         │  │  │
│                          │  │  - Network Graph     │  │  │
│                          │  │  - VEX/Python Exec   │  │  │
│                          │  └─────────────────────┘  │  │
│                          │  ┌─────────────────────┐  │  │
│                          │  │  Context Builder     │  │  │
│                          │  │  - Scene snapshot    │  │  │
│                          │  │  - Selection analysis│  │  │
│                          │  │  - JSON serializer   │  │  │
│                          │  └─────────────────────┘  │  │
│                          │  ┌─────────────────────┐  │  │
│                          │  │  Action Engine       │  │  │
│                          │  │  - ACPY mode         │  │  │
│                          │  │  - Confirm + Execute │  │  │
│                          │  │  - Undo stack        │  │  │
│                          │  └─────────────────────┘  │  │
│                          └──────────┬────────────────┘  │
│                                     │                   │
└─────────────────────────────────────┼───────────────────┘
                                      │ HTTPS / localhost
                               ┌──────▼──────┐
                               │  AI Provider │
                               │ (可切换)     │
                               └─────────────┘
```

## 与参考工具对比后的关键改进点

以下是通过分析 rart.gumroad.com/HoudiniAIAssistant 后确认的差距和改进：

| # | 参考工具特性 | 我们原计划的差距 | 改进方案 |
|---|------------|---------------|---------|
| 1 | 多 AI 后端（Claude/GPT/DeepSeek/Gemini/Ollama） | 原计划只支持 Claude | 从 v0.1 起设计 Provider 抽象层 |
| 2 | 本地模型支持（Ollama/LM Studio） | 无此计划 | 加入 Provider 层，支持 OpenAI 兼容 API |
| 3 | ACPY Action Mode（前缀触发执行） | 原计划用 Tool Use 回调 | 加入 ACPY 前缀模式，对话 vs 执行双模式 |
| 4 | Context Status 指示器 | 无 | 显示 AI 当前"看到"的场景状态 |
| 5 | Roles 系统（Scene Analyst / Debugger / Documenter） | 无角色区分 | 定义角色模板，影响 System Prompt |
| 6 | Debug Selection 功能 | 无专门调试 | 专用 Debug 流程：分析上游错误链 |
| 7 | 文档生成（Export as HTML/PDF） | 无导出功能 | 加入 Documentation Generator |
| 8 | Advanced Export（JSON 序列化 + 粒度控制） | 无导出功能 | 上下文 JSON 导出，可配置范围/深度 |
| 9 | HDA from Prompt（MoE: Architect→Builder→Validator） | 原计划 v0.3 才有模板 | 提前到 v0.2，用多步 Agent 流程 |
| 10 | Qt5/PySide2 + Qt6/PySide6 双支持 | 只提 PySide2 | 做兼容层，支持 Houdini 20.5 + 21+ |
| 11 | Token 用量实时计数 | 无 | 底栏显示 session token 统计 |
| 12 | Prompt 可编辑（UI 中修改 System Prompt） | 无此功能 | 设置面板中开放 System Prompt 编辑 |
| 13 | RAG（索引用户项目/HDA） | 无此计划 | v0.3 加入本地 RAG |
| 14 | Splash Screen 启动面板 | 直接进入聊天 | 加启动面板：快速入口 + 文档 + 示例 Prompt |

---

## 关键技术点

### 1. 与 Houdini 交互 — HOM API
- `hou.selectedNodes()` — 获取选中节点
- `hou.node(path)` — 获取/创建节点
- `parm.set()` / `parm.setExpression()` — 修改参数
- `node.setInput()` — 连接节点
- `hou.hscript()` — 执行 hscript 命令
- `hou.hdaDefinition()` / `hou.HDADefinition()` — HDA 操作
- 所有操作通过 `hou` 模块完成

### 2. Qt 兼容层
- Houdini 20.5 及以下：PySide2 (Qt5)
- Houdini 21+：PySide6 (Qt6)
- 统一封装为 `hai.qt_compat`，自动检测并 import 正确版本

```python
# hai/qt_compat.py
try:
    from PySide6 import QtWidgets, QtCore, QtGui
except ImportError:
    from PySide2 import QtWidgets, QtCore, QtGui
```

### 3. AI Provider 抽象层
- 统一的 `ProviderInterface`：send_message / stream_message / count_tokens
- 每个 Provider 独立适配（Anthropic / OpenAI / DeepSeek / Gemini / Ollama）
- 本地模型走 OpenAI 兼容 API（Ollama 和 LM Studio 都支持）
- Provider 选择器在 UI 设置面板中切换

### 4. ACPY Action Mode
- **普通模式**：AI 只回答、解释、建议，不执行操作
- **ACPY 模式**：prompt 以 `ACPY:` 开头时，AI 返回操作指令，自动执行
- 执行前弹窗确认，显示将要执行的操作清单
- 支持 Undo

### 5. Roles 系统
- **Scene Analyst** — 分析场景结构，解释数据流
- **Debugger** — 诊断错误，定位根因
- **Technical Documenter** — 生成技术文档
- **Code Generator** — VEX/Python 代码生成
- **HDA Architect** — HDA 设计（MoE 多步流程）
- 每个 Role 对应不同的 System Prompt 模板

### 6. 安全机制
- 代码执行默认关闭（`Allow Code Execution` 开关）
- 开启后，执行前仍需逐次确认
- 危险操作（删除节点、批量修改）需用户确认
- 操作日志记录，支持 Undo
- 可配置权限级别：只读 / 受限操作 / 完全控制
- 本地模型模式：数据不出本机

---

## 版本计划

### v0.1 — MVP：对话 + 基础节点操作 + 多后端
**目标：能对话，能查，能建节点，支持多个 AI 后端**

- [ ] 项目脚手架
  - Houdini Shelf 按钮一键加载插件
  - Qt 兼容层（PySide2/PySide6）
  - 包结构和安装脚本
- [ ] Splash Screen 启动面板
  - 快速入口：Start Assistant / Settings / Sample Prompts / Docs
- [ ] UI 面板（Chat Panel）
  - 聊天窗口（消息列表 + Markdown 渲染 + 输入框）
  - 嵌入 Houdini 作为 Pane Tab
  - 顶栏：Context Status | Clear Chat | Settings
  - 底栏：Analyze Context | Analyze Selection | Response Style | Send | Token Counter
- [ ] Settings 面板
  - API Key 输入和验证
  - Provider 选择器（Claude / OpenAI / DeepSeek / Gemini / Ollama / LM Studio）
  - System Prompt 可编辑区域
  - Allow Code Execution 开关
- [ ] AI Provider 抽象层
  - `ProviderInterface` 基类
  - Claude Provider（Anthropic SDK，Tool Use）
  - OpenAI Provider（GPT 系列，Function Calling）
  - Ollama Provider（本地，OpenAI 兼容 API）
- [ ] Context Builder（场景上下文）
  - 序列化选中节点（路径、类型、参数、连接）
  - 序列化场景全局上下文
  - JSON 格式输出
- [ ] Tool 定义（第一批）
  - `get_selected_nodes` — 返回选中节点路径和类型
  - `get_node_info` — 查询节点参数详情
  - `create_node` — 在指定路径创建节点
  - `set_parameter` — 修改节点参数值
  - `connect_nodes` — 连接两个节点
- [ ] ACPY Action Mode
  - 检测 `ACPY:` 前缀
  - 操作确认弹窗
  - 执行 + 结果反馈
- [ ] 操作确认机制
  - 写操作弹出确认提示
  - 显示即将执行的操作描述

### v0.2 — 场景感知 + HDA 生成 + 调试
**目标：AI 深度理解场景，能生成 HDA，能调试**

- [ ] 场景上下文增强
  - `get_node_tree` — 获取节点树结构
  - `get_subnetwork` — 深入子网络
  - 增量上下文更新（不重复发送）
- [ ] 更多 Tool
  - `delete_node` — 删除节点
  - `copy_node` / `paste_node` — 复制粘贴节点
  - `set_expression` — 设置参数表达式
  - `run_python` — 执行任意 Python 脚本（需确认）
  - `run_hscript` — 执行 hscript
  - `set_keyframe` — 设置关键帧
- [ ] Roles 系统
  - Scene Analyst / Debugger / Documenter / Code Generator
  - 每个 Role 对应 System Prompt 模板
  - UI 中可切换 Role
- [ ] Debug Selection
  - 分析选中节点及其上游链路
  - 检测 warnings / errors
  - 返回根因 + 修复建议
- [ ] HDA from Prompt（MoE 流程）
  - Architect → Builder → Validator 三步流程
  - Architect：设计 HDA 结构和参数
  - Builder：创建节点、连线、设参数、打包 HDA
  - Validator：检查完整性，自修正错误
  - 支持 promoted parameters
- [ ] Documentation Generator
  - 从选中节点生成技术文档
  - 输出为 HTML / Markdown
- [ ] Advanced Export
  - 场景 JSON 序列化导出
  - 粒度控制：范围（全场景/选中）、递归深度、仅修改参数、属性信息等
- [ ] Undo 支持
  - 每次操作前自动创建 Undo 栈

### v0.3 — RAG + CoT + 高级生产力
**目标：知识增强，推理增强，专业级工具**

- [ ] RAG（检索增强生成）
  - 索引用户项目文件夹和 HDA 库
  - 查询时检索相关文档和代码
  - 支持本地 embedding（不依赖云服务）
  - AI 回答时基于用户自己的项目上下文
- [ ] Chain of Thought（CoT）
  - 可视化推理步骤
  - UI 中展示思考过程
  - 复杂问题的分步解答
- [ ] 智能建议
  - 根据当前上下文主动建议工作流
  - "你选中了一个 Grid SOP，要不要加一个 Mountain？"
- [ ] 节点预设模板
  - 常用节点组合一键生成（地形、粒子、破碎等）
  - 用户自定义模板保存
- [ ] VEX / Python 生成增强
  - 带性能分析的代码建议
  - "把慢链路转成 VEX Wrangle"
- [ ] 多轮复杂任务
  - 支持复杂多步骤任务（"帮我搭一个雨效果"）
  - 中间步骤可暂停、调整、继续

### v0.4 — 协作与扩展
**目标：可定制、可分享、生产就绪**

- [ ] 自定义 Tool 注册
  - 用户可以写自己的 Tool 函数注册给 AI
- [ ] 模板市场 / 分享
  - 导出/导入节点模板
  - 分享 Prompt 配置和 Role 模板
- [ ] 更多 Provider
  - 补全 Gemini / Mistral / 其他 OpenAI 兼容模型
- [ ] MoE 增强
  - 专用 AI：VEX 专家 / Python 专家 / procedural 专家 / 性能专家
  - 自动路由到合适的专家
- [ ] 多语言 UI 支持（中/英）
- [ ] 性能优化
  - 大场景下的上下文裁剪
  - 增量更新场景快照
  - 流式响应（SSE streaming）
- [ ] 学习模式
  - 记录用户操作习惯
  - 生成可复用的 Python 脚本

---

## 目录结构规划

```
HoudiniAIAssistant/
├── PROJECT_PLAN.md              # 本文件
├── README.md                    # 使用说明
├── requirements.txt             # Python 依赖
│
├── pythonpath/                  # 放入 HOUDINI_PATH 的 pythonpath 目录
│   └── hai/                     # 主包 (Houdini AI)
│       ├── __init__.py
│       ├── qt_compat.py         # PySide2/PySide6 兼容层
│       │
│       ├── providers/           # AI 后端抽象层
│       │   ├── __init__.py
│       │   ├── base.py          # ProviderInterface 基类
│       │   ├── claude.py        # Anthropic Claude (Tool Use)
│       │   ├── openai.py        # OpenAI GPT (Function Calling)
│       │   ├── deepseek.py      # DeepSeek
│       │   ├── gemini.py        # Google Gemini
│       │   ├── ollama.py        # Ollama 本地模型
│       │   └── lmstudio.py      # LM Studio 本地模型
│       │
│       ├── agent.py             # Agent 核心：消息循环、Tool 调度
│       ├── roles.py             # Roles 系统：System Prompt 模板
│       ├── acpy.py              # ACPY Action Mode 引擎
│       │
│       ├── tools/               # Tool 定义（供 AI 调用）
│       │   ├── __init__.py
│       │   ├── registry.py      # Tool 注册表
│       │   ├── node_ops.py      # 节点 CRUD
│       │   ├── param_ops.py     # 参数读写
│       │   ├── scene_query.py   # 场景查询
│       │   ├── exec_ops.py      # Python/hscript 执行
│       │   ├── hda_ops.py       # HDA 操作
│       │   └── debug_ops.py     # 调试工具
│       │
│       ├── context.py           # 场景上下文构建 + JSON 序列化
│       ├── export.py            # 文档导出（HTML/Markdown/PDF）
│       │
│       ├── ui/                  # Qt UI
│       │   ├── __init__.py
│       │   ├── splash.py        # 启动面板
│       │   ├── chat_panel.py    # 聊天面板主窗口
│       │   ├── settings.py      # 设置面板
│       │   ├── confirm_dialog.py # 操作确认弹窗
│       │   └── styles.py        # QSS 样式（Houdini 风格暗色主题）
│       │
│       ├── config.py            # 配置管理（API Key、Provider、偏好）
│       └── permissions.py       # 权限与确认机制
│
├── shelf/                       # Houdini Shelf 定义
│   └── HoudiniAIAssistant.shelf
│
├── prompts/                     # Prompt 模板
│   ├── system_base.md           # 基础 System Prompt
│   ├── role_analyst.md          # Scene Analyst 角色模板
│   ├── role_debugger.md         # Debugger 角色模板
│   ├── role_documenter.md       # Documenter 角色模板
│   ├── role_coder.md            # Code Generator 角色模板
│   └── role_hda_architect.md    # HDA Architect 角色模板
│
└── tests/                       # 测试
    ├── test_tools.py
    ├── test_agent.py
    ├── test_context.py
    └── test_providers.py
```

## 开发环境要求

- **Houdini** 20.0+（支持 Qt5 和 Qt6 双模式）
- **Python** 3.10+（Houdini 内置）
- **依赖包：**
  - `anthropic` — Claude API
  - `openai` — OpenAI / DeepSeek / Ollama 兼容 API
  - `google-generativeai` — Gemini API（可选）
- **用户需自备至少一种：**
  - AI Provider API Key（Anthropic / OpenAI / DeepSeek / Google 之一）
  - 或本地模型服务（Ollama / LM Studio）

## 快速开始（v0.1 目标）

1. 将 `pythonpath/` 目录加入 `HOUDINI_PATH` 环境变量
2. 在 Houdini 中点击 Shelf 按钮 → 打开 Splash Screen
3. 点击 Settings → 输入 API Key → 选择 Provider
4. 点击 Start Assistant → 开始对话
5. 选中节点 → 点击 "Analyze Selection" → 获取场景分析
6. 或使用 ACPY 模式：`ACPY: 在选中节点后加一个 Null`

## 我们的差异化（vs 参考工具）

| 方面 | 参考工具 | 我们的改进方向 |
|------|---------|-------------|
| 开源 | 闭源付费 | **完全开源免费** |
| 语言 | 英文为主 | **中文优先 + 双语支持** |
| 安装 | 手动配置路径 | 一键安装脚本 |
| HDA 生成 | 单步 / MoE | MoE + 自修正循环 |
| RAG | 计划中 | 更早引入，本地优先 |
| 代码质量 | 未知 | 开源可审查，测试覆盖 |

---

## 当前问题记录

### UI 集成崩溃 (2026-04-26)

**环境**: Houdini 20.5.487, PySide2 (Qt5), Windows 10

**现象**: 插件启动直接导致 Houdini 崩溃 (segfault)

**诊断结果** (见 `tests/diagnose_crash.py` + `tests/crash_log.txt`):
- `hou.ui.registerViewerPaneTab` — 该 API 在 20.5.487 中**不存在**
- 无 parent 的 `QWidget().show()` 直接触发 segfault（Step 8 崩溃）
- `setParent + Qt.Window + show` 方案未测试到（Step 9 未执行）
- 结论：Houdini 的 Qt 事件循环要求所有 widget 必须有正确的 parent

**解决方案**: Python Panel Interface（`.pypanel`）
- 这是 Houdini 最正统的嵌入方式（Houdini 14+ 就支持）
- `.pypanel` 文件放在 `pythonpath/python_panels/` 目录，Houdini 自动发现
- `createInterface()` 函数返回 widget，Houdini 管理 parent 和生命周期
- 通过 `hou.pypanel.interfacesByName()` + `pane.createTab()` 打开
- 不存在 parent 问题，也不需要 `registerViewerPaneTab`

**涉及改动的文件**:
- `pythonpath/python_panels/hai_assistant.pypanel` — 新建，面板接口定义
- `pythonpath/hai/ui/chat_panel.py` — 移除 registerViewerPaneTab，改用 Python Panel API
- `pythonpath/hai/__init__.py` — 入口函数改用 Python Panel API
- `shelf/HoudiniAIAssistant.py` — Shelf 按钮改用 Python Panel API 打开面板
