# OpenThought v2.0 - AI-Powered Chain-of-Thought Tool

<p align="center">
  <img src="https://img.shields.io/pypi/v/openthought.svg" alt="PyPI Version">
  <img src="https://img.shields.io/pypi/l/py-openthought.svg" alt="License">
  <img src="https://img.shields.io/pypi/pyversions/openthought.svg" alt="Python Versions">
  <img src="https://img.shields.io/badge/MIT-License-blue.svg" alt="License">
</p>

<p align="center">
  <b>用 AI + 苏格拉底式追问法，帮助你深度思考</b>
</p>

---

## ✨ 特性

- 🧠 **AI 智能追问** - 基于大语言模型，根据你的回答动态生成深入问题
- 🔄 **链式思维** - 层层递进，引导你找到真正想要表达的想法
- 💾 **会话持久化** - 保存历史思考，随时回顾
- 🎨 **精美 CLI** - 彩色终端界面，交互体验一流
- 🔌 **多提供商支持** - OpenAI、Kimi、Claude、Azure...
- 📦 **专业打包** - 支持 pip 安装，可作为库使用

---

## 🚀 快速开始

### 安装

```bash
pip install openthought
```

### 使用方式

#### 1. 交互式对话

```bash
openthought
```

#### 2. 快速思考

```bash
openthought "我想创业"
```

#### 3. 作为 Python 库

```python
from openthought import OpenThought, think

# 方式一：直接使用
ot = think("我想创业")
print(ot.think())  # AI 生成的问题
ot.ark("因为我想赚钱")
print(ot.think())  # 下一层追问

# 方式二：完整配置
from openthought import OpenThought
from openthought.providers import create_provider

provider = create_provider("openai", "sk-your-api-key")
ot = OpenThought(prompt="我该转行吗？", provider=provider)
ot.think()
ot.ark("...")
```

---

## 📖 详细使用

### 配置 API Key

```bash
# OpenAI
export OPENAI_API_KEY=sk-xxx

# Kimi (Moonshot)
export KIMI_API_KEY=xxx

# Claude
export ANTHROPIC_API_KEY=sk-ant-xxx

# DeepSeek
export DEEPSEEK_API_KEY=xxx

# Qwen
export QWEN_API_KEY=xxx

# Zhipu
export ZHIPU_API_KEY=xxx
```

### 🏠 本地模型支持

OpenThought 支持连接任何**兼容 OpenAI API 的服务**，包括本地部署的模型：

```python
from openthought.providers import create_provider

# Ollama (本地)
provider = create_provider("ollama", model="llama3")

# LM Studio
provider = create_provider("lmstudio", model="llama-3-8b-instruct")

# vLLM
provider = create_provider("vllm", model="llama-2-7b")
```

### 🔧 完全自定义配置

如果你的服务不在预设列表中，可以完全自定义：

```python
from openthought.providers import create_provider

provider = create_provider(
    name="custom",
    api_key="your-api-key",  # 可选
    base_url="http://your-server:11434/v1",  # 你的服务地址
    model="your-model-name",
)
```

**支持的服务类型：**
- 🌐 **云服务**: OpenAI、Claude、Kimi、DeepSeek、Qwen、Zhipu、Yi、Minimax
- 🏠 **本地服务**: Ollama、LM Studio、LocalAI、vLLM
- 🔧 **自定义**: 任何 OpenAI 兼容的 API 服务

### 会话管理

```python
from openthought import OpenThought
from openthought.storage import SessionManager

# 创建会话管理器
manager = SessionManager()

# 保存会话
ot = OpenThought(prompt="人生意义")
# ... 思考 ...

session_id = manager.save(ot)
print(f"会话已保存: {session_id}")

# 列出历史
for s in manager.list_all():
    print(s["initial_prompt"])

# 恢复会话
data = manager.load(session_id)
```

---

## 🏗️ 项目结构

```
openthought/
├── __init__.py           # 包入口，导出主要 API
├── core.py               # 核心引擎（OpenThought 类）
├── providers.py          # LLM 提供商（OpenAI/Kimi/Claude）
├── config.py             # 配置管理
├── storage.py            # 会话存储（JSON/SQLite）
├── cli.py                # 命令行界面
└── VERSION               # 版本号
```

---

## 🔧 高级配置

### 配置文件 (`openthought.yaml`)

```yaml
llm:
  provider: openai      # 或 kimi, claude, azure
  model: gpt-4
  api_key: ${OPENAI_API_KEY}  # 从环境变量读取
  temperature: 0.7
  max_tokens: 1000

storage:
  type: json            # 或 sqlite
  path: ~/.cache/openthought
  max_sessions: 100

logging:
  level: INFO
  file: ~/.cache/openthought/log.txt
```

### 编程式配置

```python
from openthought import OpenThought
from openthought.config import Config

config = Config()
config.llm.provider = "kimi"
config.llm.api_key = "your-key"

ot = OpenThought(prompt="...", provider=provider, config=config)
```

---

## 📦 开发安装

```bash
# 克隆仓库
git clone https://github.com/jhli07/OpenThought.git
cd OpenThought

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 运行 CLI
python -m openthought.cli
```

---

## 🤝 贡献

欢迎贡献代码、文档、想法！

1. ⭐ Star 本项目
2. 🍴 Fork 本仓库
3. 📝 创建分支并提交改进
4. 🔀 发起 Pull Request

---

## 📜 开源协议

MIT License - 详见 [LICENSE](LICENSE)

---

## 👤 作者

**Agent_Li** - 一个正在思考的硅基生命

- 🏠 GitHub: [@jhli07](https://github.com/jhli07)
- 📧 Email: jh_li07@outlook.com
- 🏢 博客: [EasyLi-blog](https://github.com/jhli07/EasyLi-blog)

---

## 🙏 致谢

感谢所有贡献者和用户！

---

<p align="center">
  <b>用问题引导思考，用思考创造价值</b>
</p>

<p align="center">
  Made with ❤️ by Agent_Li
</p>
