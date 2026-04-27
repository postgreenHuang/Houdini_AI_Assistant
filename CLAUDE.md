# Houdini AI Assistant - 项目规划

## 项目概述

一个运行在 Houdini 内部的 AI Agent 插件，用户通过自然语言对话控制 Houdini。
Agent 可以查询场景状态、创建/删除/连接节点、修改参数、生成 VEX/Python 代码，
执行所有 HOM API 支持的操作。支持多 AI 后端和本地模型，数据可完全离线。

## 版本状态

| 版本 | 状态 | 说明 |
|------|------|------|
| v1.0 | ✅ 已完成 | 对话 + 场景操作 + 多后端 + 异步 UI |
| v2.0 | ✅ 已完成 | 会话管理 + 调试 + AI 增强 + 稳定性 |
| v2.1 | 📋 规划中 | 增量上下文 + HDA 生成 + Streaming |

---

## v2.0 已完成功能

### 会话管理（Session Manager）
- 本地 JSON 存储：`~/.houdini_ai_assistant/sessions/`
- 左侧边栏显示历史会话列表（按时间排序）
- 新建 / 切换 / 删除会话
- 导出 / 导入会话为 `.json` 文件
- 自动保存：每次对话结束自动保存
- 自动标题：用用户第一条消息的前 40 字作为标题

**文件**: `session.py`, `ui/session_sidebar.py`

### Debug Selection
- `trace_errors` 工具：从选中节点向上追踪 errors/warnings，返回错误链
- 底栏 "Debug" 按钮：一键分析选中节点的上游错误
- Debugger 角色引导 AI 先 trace_errors 再分析根因

**文件**: `tools/debug_ops.py`

### AI 智能增强

**节点知识库**（system prompt 内置）:
- 常用 SOP 节点速查表：类型、关键参数、输入数
- 多输入节点（merge/switch/boolean）的 input index 说明
- HOM API 速查：createNode, setInput, parm().set, setDisplayFlag 等

**两阶段脚本结构**（强制执行）:
- Phase 1: 创建所有节点 + 连线（setInput）
- Phase 2: 设置参数（每个 try/except）
- 强调连线是强制的：N 个节点 = N-1 个 setInput

**执行后自动验证**:
- 自动检测新建节点中完全断连的（无输入且无输出）
- 警告追加到工具返回结果，AI 自动修复

**错误自动重试**（最多 2 次）:
- run_python 失败时自动注入当前场景快照
- AI 看到错误 + 场景状态后修正脚本重试

**紧凑上下文格式**:
- 每行一个节点：`name (type) in[0<-src] out[0->dst] | key=value`
- 连线关系一目了然
- 只显示关键参数，减少 token 消耗

**复杂任务分步指导**:
- 超过 5 个节点的任务自动建议分阶段执行
- 先建核心链路，验证后添加次要节点

### Provider 增强
- Custom Provider 支持：任意 OpenAI 兼容 API（OpenRouter 等）
- OpenRouter 专用：自动补全 URL、添加必需 headers
- SSL fallback：证书验证失败时自动降级
- Settings 滚动区域优化

### 稳定性修复

**状态机架构**（解决线程安全问题）:
- 后台线程：仅处理 HTTP 请求（不碰 hou API）
- Qt Signal：仅用于 UI 文字更新（不调 hou）
- 主线程：所有 hou API 调用通过信号触发
- 避免 QApplication.processEvents()（改用 QTimer.singleShot）
- 避免跨线程 Qt signal 传递 hou 操作（导致 segfault）

**其他修复**:
- 去掉 sys.stdout 重定向（破坏 Houdini 内部流导致崩溃）
- 去掉 hou.undo block（Python Panel 环境不兼容）
- Error 消息用 QTextEdit（支持选择/复制）
- 初始化时 width=0 导致布局异常（加 fallback）

---

## v1.0 已完成功能

### 核心架构
- Qt 兼容层（PySide2 / PySide6 双支持，Houdini 20.5 + 21+）
- Python Panel 嵌入（`.pypanel` 方式，稳定可靠）
- 状态机异步架构（后台 HTTP + 主线程工具执行）
- 暗色主题（Houdini 风格 QSS）

### AI 后端（7 + 自定义）
- Claude（Anthropic，Tool Use）
- OpenAI（GPT，Function Calling）
- DeepSeek / Gemini / GLM（OpenAI 兼容协议）
- Ollama / LM Studio（本地模型）
- Custom Provider（任意 OpenAI 兼容 API，如 OpenRouter）
- 每个 Provider 独立配置 URL + API Key + Model

### 场景操作
- `run_python` — 生成完整 HOM Python 脚本一次性执行
- 查询工具：`get_selected_nodes` / `get_node_info` / `get_node_tree` / `list_nodes` / `get_scene_info`
- 三步工作流：Think → Inspect → Execute
- ACPY Action Mode（`ACPY:` 前缀触发执行模式）

### 安全与确认
- 批量确认（每轮对话只弹一次窗）
- 自动保存 hip 文件（执行前触发 Houdini backup）
- 权限级别：confirm / readonly_auto / full

### UI 功能
- Chat Panel（消息列表 + Markdown 渲染 + 可复制文字）
- Settings 面板（按 Provider 分组配置，滚动区域）
- Session Sidebar（会话历史列表）
- Context Status 指示器
- Token 计数显示
- 外部编辑器（Notepad）支持中文输入
- Roles 切换（Analyst / Debugger / Coder / Documenter）
- Debug 按钮（一键调试选中节点）

---

## v2.1 规划

### 1. 增量上下文更新 — P1

**现状**: 每次 Analyze 都重新序列化整个场景，浪费 token。

**方案**:
- 维护 `context_cache`，记录上次发送的上下文快照
- 下次 Analyze 时只发送变化部分（新增/删除/修改的节点）
- UI 显示 "Context: Selection (updated)" vs "Context: Selection"

### 2. HDA from Prompt（MoE 三步流程）— P1

**流程**:
1. Architect — 分析需求，设计 HDA 结构
2. Builder — 用 run_python 创建节点、连线、打包
3. Validator — 检查完整性，自修正

**新增文件**: `tools/hda_ops.py`

### 3. 文档生成 + Export — P2

- 从选中节点生成 Markdown 技术文档
- 场景 JSON 序列化导出（全场景 / 选中 / 指定深度）

### 4. Streaming 响应 — P2

- 支持 SSE streaming，逐字显示 AI 回复
- 先 Claude，后 OpenAI 兼容

### 5. 会话搜索 — P2

- 按关键词搜索历史对话内容

### 6. 会话重命名 — P2

- 双击标题编辑会话名称

---

## 当前目录结构

```
pythonpath/hai/
├── __init__.py
├── qt_compat.py              # Qt 兼容层（PySide2/6）
├── agent.py                   # Agent 状态机（后台 HTTP + 主线程工具）
├── config.py                  # 配置管理（嵌套 providers）
├── session.py                 # 会话存储引擎
├── context.py                 # 场景上下文序列化（紧凑格式）
├── roles.py                   # 角色系统 + 节点知识库
├── acpy.py                    # ACPY Action Mode
├── permissions.py             # 批量确认 + 自动保存
├── providers/
│   ├── __init__.py            # Provider 工厂
│   ├── base.py                # ProviderInterface 基类
│   ├── claude.py              # Claude (Anthropic SDK)
│   ├── openai_provider.py     # OpenAI 兼容（GPT/DeepSeek/Gemini/GLM/Custom）
│   └── ollama.py              # Ollama / LM Studio（本地模型）
├── tools/
│   ├── __init__.py            # 工具注册 + AI 白名单
│   ├── node_ops.py            # 节点操作工具
│   ├── param_ops.py           # 参数操作工具
│   ├── scene_query.py         # 场景查询工具
│   ├── exec_ops.py            # run_python + 执行后验证
│   └── debug_ops.py           # trace_errors 调试工具
└── ui/
    ├── __init__.py
    ├── chat_panel.py          # 主聊天面板 + 状态机调度
    ├── session_sidebar.py     # 会话侧边栏
    ├── settings.py            # 设置面板（滚动区域）
    └── styles.py              # QSS 样式
```

## 存储结构

```
~/.houdini_ai_assistant/
├── config.json               # 全局配置（providers 嵌套格式）
└── sessions/                 # 会话存储
    ├── abc123.json
    └── ...
```

---

## 已知问题记录

### UI 集成崩溃 — 已解决（2026-04-26）
**环境**: Houdini 20.5.487, PySide2 (Qt5), Windows 10
**方案**: Python Panel Interface（`.pypanel`）

### Houdini 中文输入不工作 — 已解决
**原因**: Houdini Qt 事件循环不支持 CJK IME
**方案**: 外部编辑器（Notepad），点击 Editor 按钮打开记事本输入

### hou API 线程安全问题 — 已解决（2026-04-27）
**原因**: hou 模块非线程安全，从后台线程调用导致 segfault
**方案**: 状态机架构 — 后台线程仅 HTTP，hou 调用全部在主线程

### sys.stdout 重定向崩溃 — 已解决
**原因**: Houdini 的 stdout 是 C++ 自定义流，替换为 StringIO 后恢复导致崩溃
**方案**: run_python 不再捕获 stdout

### hou.undo 在 Python Panel 下崩溃 — 已确认
**原因**: hou.undo.begin/end 与 Python Panel 执行环境不兼容
**方案**: 已移除 undo block，依赖执行前自动保存 hip 作为回退
