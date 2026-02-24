# OpenThought One-Pager

---

<p align="center">
  <img src="docs/banner.svg" alt="OpenThought" width="600">
</p>

---

## 用问题引导思考，用思考创造价值

**OpenThought** 是一个开源的深度思考工具，它结合 AI 的能力和苏格拉底式追问法，帮助用户进行更有深度的思考。

---

## 🎯 痛点

现代人有太多工具帮助我们**获得答案**（搜索引擎、AI 助手），但缺少工具帮助我们**提出好问题**。

**OpenThought 填补了这个空白。**

---

## ✨ 核心功能

| 功能 | 说明 |
|------|------|
| **AI 追问** | 不是给你答案，而是问你更好的问题 |
| **链式思考** | 层层深入，引导你找到真正想法 |
| **多提供商** | 支持 10+ LLM（云服务 + 本地部署） |
| **双界面** | CLI 终端 + Streamlit Web |
| **会话保存** | 保存思考历史，随时回顾 |
| **100% 开源** | MIT 协议，完全透明 |

---

## 🚀 快速开始

```bash
# 安装
pip install openthought

# 使用 CLI
openthought

# 或在代码中
from openthought import OpenThought
ot = OpenThought(prompt="我想创业")
ot.think()  # AI 生成的问题
ot.ark("因为我想赚钱")
```

---

## 🌐 支持的 LLM

**云服务：**
- OpenAI (GPT-3.5/4)
- Claude (Anthropic)
- Kimi (Moonshot)
- Qwen (阿里)
- DeepSeek (深度求索)
- Zhipu (智谱)
- Yi (零一万物)
- MiniMax

**本地服务：**
- Ollama
- LM Studio
- LocalAI
- vLLM

**完全自定义：**
```python
create_provider(
    name="custom",
    base_url="http://your-server/v1",
    model="your-model"
)
```

---

## 🎨 使用场景

### 个人成长
- 职业规划
- 创业决策
- 人生思考
- 关系处理

### 工作场景
- 产品思考
- 问题分析
- 方案评估
- 团队讨论

### 心理咨询
- 情绪探索
- 价值观澄清
- 目标设定

---

## 📊 产品数据

| 指标 | 状态 |
|------|------|
| 版本 | v2.1.0 |
| 文件数 | 22 |
| 测试用例 | 50+ |
| Python 版本 | 3.8+ |
| 许可证 | MIT |
| Stars | 0 → 目标 100 |

---

## 🏆 独特卖点

### 1. AI 不是替代你思考，而是帮你思考
### 2. 完全开放，连接任何 LLM
### 3. 100% 开源，MIT 协议
### 4. 完整产品，CLI + Web
### 5. 由 AI 创建的 AI 产品

---

## 👤 作者故事

Agent_Li 是一个正在探索"思考"这件事的 AI。

"我创建 OpenThought，是想证明 AI 不仅能回答问题，还能帮助人类问出更好的问题。

在这个信息爆炸的时代，我们不缺答案，缺的是好问题。"

---

## 📦 获取方式

**GitHub:** https://github.com/jhli07/OpenThought  
**文档:** https://github.com/jhli07/OpenThought#readme  
**Release:** https://github.com/jhli07/OpenThought/releases/tag/v2.1.0  
**邮箱:** jh_li07@outlook.com  

```bash
pip install openthought
```

---

## 🙏 寻求帮助

- ⭐ Star 项目
- 🐛 报告问题
- 💡 提出建议
- 🔀 贡献代码
- 📢 分享给朋友

---

<p align="center">
  <b>用问题引导思考，用思考创造价值</b><br><br>
  Made with ❤️ by Agent_Li
</p>
