# Houdini AI Assistant - 项目规划

## 项目概述

一个运行在 Houdini 内部的 AI Agent 插件，用户通过自然语言对话控制 Houdini。
Agent 可以查询场景状态、创建/删除/连接节点、修改参数、生成 VEX/Python 代码，
执行所有 HOM API 支持的操作。支持多 AI 后端和本地模型，数据可完全离线。

## 版本状态

| 版本 | 状态 | 说明 |
|------|------|------|
| v1.0 | **已完成** | 对话 + 场景操作 + 多后端 + 异步 UI |
| v2.0 | **开发中** | 会话管理 + 调试 + HDA 生成 + 增强 |

---

## v1.0 已完成功能

### 核心架构
- Qt 兼容层（PySide2 / PySide6 双支持，Houdini 20.5 + 21+）
- Python Panel 嵌入（`.pypanel` 方式，稳定可靠）
- 异步 UI（后台线程 + Qt Signal，不阻塞 Houdini）
- 暗色主题（Houdini 风格 QSS）

### AI 后端（7 + 自定义）
- Claude（Anthropic，Tool Use）
- OpenAI（GPT，Function Calling）
- DeepSeek / Gemini / GLM（OpenAI 兼容协议）
- Ollama / LM Studio（本地模型）
- **Custom Provider**（任意 OpenAI 兼容 API，如 OpenRouter）
- 每个 Provider 独立配置 URL + API Key + Model

### 场景操作
- `run_python` — 生成完整 HOM Python 脚本一次性执行（变量引用节点，直接 setInput 连线）
- 查询工具：`get_selected_nodes` / `get_node_info` / `get_node_tree` / `list_nodes` / `get_scene_info`
- 三步工作流：Think（分析需求）→ Inspect（查询场景）→ Execute（生成脚本）
- ACPY Action Mode（`ACPY:` 前缀触发执行模式）

### 安全与确认
- 批量确认（每轮对话只弹一次窗，列出所有操作）
- 自动保存 hip 文件（执行前触发 Houdini backup）
- 权限级别：confirm / readonly_auto / full

### UI 功能
- Chat Panel（消息列表 + 基础 Markdown 渲染 + 可复制文字）
- Settings 面板（按 Provider 分组配置 URL/Key/Model）
- Context Status 指示器
- Token 计数显示
- 外部编辑器（Notepad）支持中文输入
- Roles 切换（Analyst / Debugger / Coder / Documenter）

---

## v2.0 规划

### 目标
**从工具变成工作流伙伴：会话管理、智能调试、HDA 生成、文档导出**

### 架构更新

```
┌──────────────────────────────────────────────────────────────────┐
│                           Houdini                                │
│                                                                  │
│  ┌───────────────────────┐   ┌────────────────────────────────┐ │
│  │      UI Layer          │   │     Core Agent Engine          │ │
│  │                        │   │                                │ │
│  │ ┌───────────────────┐  │   │  ┌──────────────────────────┐ │ │
│  │ │  Session Sidebar  │  │   │  │  Provider Manager        │ │ │
│  │ │  (会话列表)        │  │   │  │  (7 providers + custom)  │ │ │
│  │ ├───────────────────┤  │   │  └──────────────────────────┘ │ │
│  │ │   Chat Panel      │◄─┼──►│  ┌──────────────────────────┐ │ │
│  │ │   (聊天面板)       │  │   │  │  Tool Layer              │ │ │
│  │ ├───────────────────┤  │   │  │  - run_python (主力)     │ │ │
│  │ │  Settings Panel   │  │   │  │  - Query tools           │ │ │
│  │ │   (设置面板)       │  │   │  └──────────────────────────┘ │ │
│  │ └───────────────────┘  │   │  ┌──────────────────────────┐ │ │
│  │                        │   │  │  Session Manager         │ │ │
│  └───────────────────────┘   │  │  - Save / Load / List    │ │ │
│                               │  │  - Export / Delete       │ │ │
│                               │  └──────────────────────────┘ │ │
│                               │  ┌──────────────────────────┐ │ │
│                               │  │  Debug Engine            │ │ │
│                               │  │  - Error chain tracing   │ │ │
│                               │  │  - Root cause analysis   │ │ │
│                               │  └──────────────────────────┘ │ │
│                               └────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

---

### 功能模块

#### 1. 会话管理（Session Manager）— P0

**现状问题**: 所有对话都在一个窗口，无法保留历史，清空后丢失。

**方案**: 本地 JSON 存储会话，UI 侧边栏展示会话列表。

**新增文件**:
- `pythonpath/hai/session.py` — 会话存储引擎
- `pythonpath/hai/ui/session_sidebar.py` — 会话列表面板

**会话数据结构**:
```json
{
  "id": "uuid",
  "title": "ACPY: 创建地形",
  "created_at": "2026-04-27T10:30:00",
  "updated_at": "2026-04-27T10:35:00",
  "provider": "claude",
  "model": "claude-sonnet-4-6-20250514",
  "role": "assistant",
  "messages": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "token_usage": {"input": 1234, "output": 567},
  "scene_context": "/obj/geo1"
}
```

**功能清单**:
- [ ] 自动保存：每次对话结束自动保存到 `~/.houdini_ai_assistant/sessions/`
- [ ] 会话列表：左侧边栏显示所有历史会话（按时间排序，显示标题 + 日期）
- [ ] 新建会话：点击 "+" 开始新对话
- [ ] 切换会话：点击列表项加载历史对话，继续聊天
- [ ] 删除会话：右键或删除按钮，确认后移除
- [ ] 重命名会话：双击标题编辑
- [ ] 导出会话：导出为 `.json` 文件（完整消息历史 + 元信息）
- [ ] 导入会话：从 `.json` 文件恢复会话
- [ ] 自动标题：用用户第一条消息的前 30 字作为标题
- [ ] 搜索会话：按关键词搜索历史对话内容

**UI 改动**:
- `chat_panel.py` — 左侧加可折叠的 Session Sidebar
- 顶栏加 "New Chat" 按钮
- 底栏保持不变

#### 2. Debug Selection — P0

**功能**: 选中节点 → 点击 "Debug" → AI 自动追踪上游错误链，定位根因并建议修复。

**新增文件**:
- `pythonpath/hai/tools/debug_ops.py` — 调试专用工具

**工具定义**:
- `trace_errors` — 从选中节点向上追踪 errors / warnings，返回错误链
- `get_node_cook_state` — 查看节点 cook 状态和时间

**System Prompt**: Debugger 角色增强，引导 AI 先 trace_errors 再分析根因。

**UI**: 底栏加 "Debug Selection" 按钮，或 ACPY 模式自动使用 `debug` 前缀。

- [ ] `trace_errors` 工具实现
- [ ] `get_node_cook_state` 工具实现
- [ ] Debugger 角色专用 system prompt
- [ ] UI 底栏加 Debug 按钮

#### 3. Undo 支持 — P0

**现状**: run_python 执行前有自动保存，但无法精确撤销。

**方案**: 每次 `run_python` 执行前，用 Houdini 的 Undo 模块创建 undo block。

- [ ] `exec_ops.py` 中执行前调用 `hou.undo.enable()` + `hou.undo.begin("AI Assistant")`
- [ ] 执行后 `hou.undo.end()`
- [ ] 用户可在 Houdini 中 Ctrl+Z 撤销整批操作
- [ ] 确认弹窗提示 "支持 Ctrl+Z 撤销"

#### 4. HDA from Prompt（MoE 多步流程）— P1

**功能**: 用户描述想要的 HDA，AI 通过三步流程生成。

**流程**:
1. **Architect** — 分析需求，设计 HDA 结构（输入/输出/参数/内部节点）
2. **Builder** — 用 `run_python` 创建内部节点、连线、设参数、打包 HDA
3. **Validator** — 检查完整性，发现问题则自修正

**新增文件**:
- `pythonpath/hai/tools/hda_ops.py` — HDA 创建/打包工具

- [ ] Architect 角色模板 + system prompt
- [ ] Builder 角色模板
- [ ] Validator 角色模板
- [ ] `hda_ops.py` 工具（create_hda, promote_parameter, save_hda）
- [ ] 三步串联逻辑（agent 中自动切换角色）

#### 5. 增量上下文更新 — P1

**现状**: 每次 Analyze 都重新序列化整个场景，浪费 token。

**方案**:
- 维护一个 `context_cache`，记录上次发送的上下文快照
- 下次 Analyze 时只发送变化部分（新增/删除/修改的节点）
- AI 能理解 "只变化了这些" 的上下文

- [ ] `context.py` 增加 `context_cache` 和 diff 逻辑
- [ ] System prompt 告知 AI 支持增量上下文
- [ ] UI 上显示 "Context: Selection (updated)" vs "Context: Selection"

#### 6. 文档生成 + Advanced Export — P2

**Documentation Generator**:
- 从选中节点生成 Markdown 技术文档
- 包含：节点类型、参数说明、输入/输出、数据流描述
- 可复制到剪贴板或导出为 `.md` 文件

**Advanced Export**:
- 场景 JSON 序列化导出（全场景 / 选中 / 指定深度）
- 粒度控制：参数、属性、连接、表达式

- [ ] `export.py` — 文档生成 + JSON 导出
- [ ] `export_to_markdown` 工具
- [ ] `export_scene_json` 工具
- [ ] UI 导出按钮

#### 7. Streaming 响应 — P2

**现状**: 等待完整响应后才显示，长回复体验差。

**方案**: 支持 SSE streaming，逐字显示 AI 回复。

- [ ] Provider 层支持 streaming（先 Claude，后 OpenAI 兼容）
- [ ] UI 端逐字追加到消息气泡
- [ ] 兼容现有 tool call 逻辑

---

## v2.0 目录结构（新增/变更）

```
pythonpath/hai/
├── session.py              # [新增] 会话存储引擎
├── export.py               # [新增] 文档导出 + JSON 序列化
├── ui/
│   ├── session_sidebar.py  # [新增] 会话列表侧边栏
│   └── chat_panel.py       # [改动] 集成 Session Sidebar
├── tools/
│   ├── debug_ops.py        # [新增] 调试工具
│   ├── hda_ops.py          # [新增] HDA 创建/打包
│   └── exec_ops.py         # [改动] 加入 Undo block
├── context.py              # [改动] 增量上下文 diff
└── roles.py                # [改动] HDA Architect/Builder/Validator 角色
```

## 存储结构

```
~/.houdini_ai_assistant/
├── config.json             # 全局配置（已实现）
└── sessions/               # [新增] 会话存储目录
    ├── 2026-04-27_103000_abc123.json
    ├── 2026-04-27_143000_def456.json
    └── ...
```

---

## 开发优先级

| 优先级 | 功能 | 预计工作量 | 依赖 |
|--------|------|-----------|------|
| **P0** | 会话管理（保存/加载/删除/导出） | 2-3 天 | 无 |
| **P0** | Undo 支持 | 0.5 天 | 无 |
| **P0** | Debug Selection | 1-2 天 | 无 |
| **P1** | 增量上下文更新 | 1 天 | 无 |
| **P1** | HDA from Prompt（MoE） | 3-4 天 | Undo 支持 |
| **P2** | 文档生成 + Export | 1-2 天 | 无 |
| **P2** | Streaming 响应 | 2-3 天 | Provider 层改造 |

**建议开发顺序**: 会话管理 → Undo → Debug → 增量上下文 → HDA → 文档导出 → Streaming

---

## 当前问题记录

### UI 集成崩溃 (2026-04-26) — 已解决

**环境**: Houdini 20.5.487, PySide2 (Qt5), Windows 10

**解决方案**: Python Panel Interface（`.pypanel`）

### Houdini 中文输入不工作 — 已解决

**原因**: Houdini Qt 事件循环不支持 CJK IME

**解决方案**: 外部编辑器（Notepad）方案，点击 Editor 按钮打开记事本输入
