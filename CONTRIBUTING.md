# 贡献指南

感谢您对 OpenThought 项目的兴趣！我们欢迎各种形式的贡献。

---

## 🤝 如何贡献

### 报告问题
1. 在 [Issues](https://github.com/jhli07/OpenThought/issues) 中搜索是否已有相同问题
2. 如果没有，创建新的 Issue
3. 描述问题：
   - 复现步骤
   - 期望行为
   - 实际行为
   - 环境信息（Python 版本、操作系统等）

### 提交代码
1. Fork 本仓库
2. 创建分支: `git checkout -b feature/your-feature`
3. 编写代码并添加测试
4. 确保所有测试通过: `pytest`
5. 确保代码风格一致: `black openthought/ && isort openthought/`
6. 提交: `git commit -m "Add some feature"`
7. 推送: `git push origin feature/your-feature`
8. 创建 Pull Request

---

## 📋 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/jhli07/OpenThought.git
cd OpenThought

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装开发依赖
pip install -e ".[dev,all]"

# 运行测试
pytest

# 运行 linting
black openthought/
isort openthought/
flake8 openthought/ --max-line-length=100
mypy openthought/
```

---

## 🎯 需要的帮助

如果您想贡献代码，以下是当前需要改进的方向：

### 高优先级
- [ ] Streamlit Web 界面完善
- [ ] 更多 LLM 提供商支持
- [ ] Docker 部署支持

### 中优先级
- [ ] 性能优化
- [ ] 文档翻译（英文、日文）
- [ ] 更多测试用例

### 低优先级
- [ ] Logo 设计
- [ ] 官网搭建
- [ ] 教程视频

---

## 📐 代码规范

### Python 风格
- 遵循 PEP 8
- 使用 Black 格式化
- 使用 isort 排序 imports
- 添加类型注解（Type Hints）

### 提交信息规范
```
<type>(<scope>): <subject>

<body>

<footer>
```

类型：
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式
- `refactor`: 重构
- `test`: 测试
- `chore`: 构建/工具

---

## 🧪 测试指南

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_core.py

# 运行特定测试
pytest tests/test_core.py::TestOpenThought::test_think_without_ai

# 生成覆盖率报告
pytest --cov=openthought --cov-report=html
```

---

## 📖 文档

- API 文档使用 docstring
- 遵循 Google style docstring
- 示例代码应该可运行

```python
def example_function(param: str) -> bool:
    """
    函数简述。

    Args:
        param: 参数说明

    Returns:
        返回值说明

    Example:
        >>> example_function("test")
        True
    """
    pass
```

---

## 💬 交流

- Issue 讨论
- GitHub Discussions

---

## 📜 开源协议

本项目使用 MIT License，贡献的代码也将使用相同的协议。

---

感谢您的贡献！ 🙏
