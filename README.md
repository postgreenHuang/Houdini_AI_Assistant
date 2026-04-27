# Houdini AI Assistant

运行在 Houdini 内部的 AI Agent 插件，通过自然语言对话控制 Houdini。

## 支持的 AI 后端

| Provider | 类型 | 默认模型 |
|----------|------|---------|
| Claude (Anthropic) | 云端 | claude-sonnet-4-6 |
| OpenAI (GPT) | 云端 | gpt-4o |
| DeepSeek | 云端 | deepseek-chat |
| Google Gemini | 云端 | gemini-2.0-flash |
| GLM (智谱AI) | 云端 | glm-5.1 |
| Ollama | 本地 | llama3 |
| LM Studio | 本地 | local-model |

## 安装


### 方法：HOUDINI_PATH

找到houdini.env文件：
将 `pythonpath` 目录路径加入环境变量 `HOUDINI_PATH`：
```
HOUDINI_PATH = D:/Projects/HoudiniAIAssistant/pythonpath;&
```
在 Houdini Python Shell 中运行：

```python
import sys; sys.path.insert(0, r"D:\Projects\HoudiniAIAssistant\pythonpath"); import hai; hai.open_assistant() 
```

## 使用

### 启动插件
在任意窗口的+点击，New Pane Tab Type/Misc/Python Panel
然后这个面板的左上角，选择AI Assitant


### 首次配置

1. 点击 **Settings** 按钮
2. 选择 Provider（如 GLM）
3. 输入 API Key
4. 点击 **Save**

### 基本操作

- **普通对话**：直接输入问题，AI 会回答或解释
- **分析场景**：选中节点 → 点击 "Analyze Selection" → AI 获取上下文
- **操作模式**：输入 `ACPY: 在 /obj 下创建一个 Box` → AI 自动创建节点
- **切换角色**：顶栏 Role 下拉框切换（Analyst / Debugger / Coder / Documenter）

### GLM (智谱AI) 使用

1. Settings → Provider 选择 **GLM**
2. 输入从 [open.bigmodel.cn](https://open.bigmodel.cn) 获取的 API Key
3. Model 可填 `glm-5.1`（默认）、`glm-4-plus`、`glm-4` 等
4. Save 后即可使用

## 项目结构

```
HoudiniAIAssistant/
├── install.py                   # 安装脚本
├── HoudiniAIAssistant.json      # Houdini 包配置
├── pythonpath/hai/              # 主包
│   ├── __init__.py              # 入口函数
│   ├── agent.py                 # Agent 核心
│   ├── config.py                # 配置管理
│   ├── context.py               # 场景上下文
│   ├── providers/               # AI 后端
│   ├── tools/                   # HOM 工具
│   ├── ui/                      # Qt 界面
│   └── ...
├── prompts/                     # Prompt 模板
├── shelf/                       # Shelf 工具
└── tests/                       # 测试
```

## 要求

- Houdini 20.0+
- Python 3.10+（Houdini 内置）
- 至少一个 AI 后端的 API Key 或本地模型服务
