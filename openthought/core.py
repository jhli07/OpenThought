"""
OpenThought Core Engine v3.0 - AI-Powered Chain-of-Thought Implementation.

Refactored for:
- Streaming support
- Async/await
- Better error handling
- Plugin system
"""

import asyncio
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional, Protocol, Type, runtime_checkable


class OpenThoughtError(Exception):
    """Base exception for OpenThought."""
    pass


class ConfigurationError(OpenThoughtError):
    """Raised when configuration is invalid."""
    pass


class ProviderError(OpenThoughtError):
    """Raised when LLM provider fails."""
    pass


class RateLimitError(ProviderError):
    """Raised when API rate limit exceeded."""
    def __init__(self, retry_after: int = 0):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds.")


class TimeoutError(ProviderError):
    """Raised when request times out."""
    pass


class ThinkingStyle(Enum):
    """Enum for different thinking strategies."""
    SOCRATIC = "socratic"           # 苏格拉底式
    COACH = "coach"                 # 教练式
    WHY_5 = "5whys"                 # 5个为什么
    DECISION_MATRIX = "decision"    # 决策矩阵
    PRO_CON = "procon"              # 利弊分析


@dataclass
class Message:
    """A single message in the conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        return cls(
            role=data.get("role", "user"),
            content=data.get("content", ""),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Savepoint:
    """A savepoint in the thinking process for branching."""
    id: str
    name: str
    timestamp: str
    message_count: int
    question: str
    answer: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "timestamp": self.timestamp,
            "message_count": self.message_count,
            "question": self.question,
            "answer": self.answer,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Savepoint":
        return cls(**data)


@dataclass
class Session:
    """
    A thinking session with branching support.
    
    Attributes:
        id: Unique session identifier
        initial_prompt: The original question/topic
        messages: List of conversation messages
        savepoints: Savepoints for branching
        created_at: Session creation timestamp
        updated_at: Last update timestamp
        metadata: Optional additional metadata
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    initial_prompt: str = ""
    messages: List[Message] = field(default_factory=list)
    savepoints: List[Savepoint] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    thinking_style: ThinkingStyle = ThinkingStyle.SOCRATIC
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None) -> None:
        """Add a message to the session."""
        self.messages.append(Message(
            role=role,
            content=content,
            metadata=metadata or {}
        ))
        self.updated_at = datetime.now().isoformat()
    
    def add_savepoint(self, name: str, question: str, answer: Optional[str] = None) -> str:
        """Add a savepoint for branching."""
        sp = Savepoint(
            id=str(uuid.uuid4())[:8],
            name=name,
            timestamp=datetime.now().isoformat(),
            message_count=len(self.messages),
            question=question,
            answer=answer,
        )
        self.savepoints.append(sp)
        return sp.id
    
    def restore_to_savepoint(self, savepoint_id: str) -> int:
        """Restore to a savepoint. Returns number of messages removed."""
        for i, sp in enumerate(self.savepoints):
            if sp.id == savepoint_id:
                removed = len(self.messages) - sp.message_count
                self.messages = self.messages[:sp.message_count]
                self.updated_at = datetime.now().isoformat()
                return removed
        raise OpenThoughtError(f"Savepoint not found: {savepoint_id}")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "initial_prompt": self.initial_prompt,
            "messages": [m.to_dict() for m in self.messages],
            "savepoints": [s.to_dict() for s in self.savepoints],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
            "thinking_style": self.thinking_style.value,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        messages = [Message.from_dict(m) for m in data.get("messages", [])]
        savepoints = [Savepoint.from_dict(s) for s in data.get("savepoints", [])]
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            initial_prompt=data.get("initial_prompt", ""),
            messages=messages,
            savepoints=savepoints,
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            metadata=data.get("metadata", {}),
            thinking_style=ThinkingStyle(data.get("thinking_style", "socratic")),
        )
    
    def to_llm_messages(self) -> List[Dict[str, str]]:
        """Convert to LLM message format."""
        messages = []
        if self.initial_prompt:
            messages.append({"role": "system", "content": f"用户想要思考的主题: {self.initial_prompt}"})
        messages.extend([{"role": m.role, "content": m.content} for m in self.messages])
        return messages
    
    def export_markdown(self) -> str:
        """Export session as Markdown."""
        lines = [
            f"# 思考会话: {self.initial_prompt}",
            "",
            f"**创建时间**: {self.created_at}",
            f"**更新时间**: {self.updated_at}",
            f"**问答轮次**: {len([m for m in self.messages if m.role == 'user'])}",
            "",
            "---",
            "",
            "## 对话记录",
            "",
        ]
        
        user_messages = [m for m in self.messages if m.role == "user"]
        assistant_messages = [m for m in self.messages if m.role == "assistant"]
        
        for i, (q, a) in enumerate(zip(assistant_messages, user_messages), 1):
            lines.append(f"### 第 {i} 轮")
            lines.append("")
            lines.append(f"**Q**: {q.content}")
            lines.append("")
            lines.append(f"**A**: {a.content}")
            lines.append("")
            lines.append("---")
            lines.append("")
        
        return "\n".join(lines)
    
    def export_html(self) -> str:
        """Export session as HTML."""
        md = self.export_markdown()
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{self.initial_prompt}</title>
    <style>
        body {{ font-family: system-ui, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; }}
        h3 {{ color: #666; }}
        blockquote {{ background: #f5f5f5; padding: 10px; border-left: 4px solid #007bff; }}
        hr {{ border: none; border-top: 1px solid #eee; }}
    </style>
</head>
<body>
    <pre>{md}</pre>
</body>
</html>"""


@runtime_checkable
class BaseLLMProvider(Protocol):
    """Protocol for LLM providers."""
    
    @abstractmethod
    def generate(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> str:
        """Generate a response from the LLM."""
        ...
    
    @abstractmethod
    async def agenerate(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> str:
        """Async generate a response."""
        ...
    
    @abstractmethod
    async def astream_generate(
        self, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream generate responses."""
        ...
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Get the model name."""
        ...
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Get the provider name."""
        ...


class OpenThought:
    """
    AI-Powered Chain-of-Thought Tool v3.0.
    
    New features:
    - Streaming support
    - Async/await
    - Multiple thinking styles
    - Savepoints & branching
    - Plugin system
    
    Example:
        >>> ot = OpenThought(prompt="我想创业")
        >>> async for chunk in ot.athink():
        >>>     print(chunk, end="", flush=True)
    """
    
    VERSION = "3.0.0"
    
    # Default Socratic questions by depth level
    DEFAULT_QUESTIONS_BY_DEPTH = {
        0: ["什么让你想到这个？", "你能具体说说吗？"],
        1: ["为什么这对你很重要？", "这和你的核心价值观有什么关系？"],
        2: ["如果实现这个，你的感受会怎样？", "谁会因为这个决定受到影响？"],
        3: ["你觉得最大的挑战是什么？", "你有没有从另一个角度想过这个问题？"],
        4: ["如果你的朋友遇到同样的问题，你会怎么建议他？", "一年后的你，会怎么看今天的这个问题？"],
        5: ["你有没有忽略什么重要的因素？", "最终，你想要达成的是什么？"],
    }
    
    # Thinking style prompts
    STYLE_PROMPTS = {
        ThinkingStyle.SOCRATIC: """你是一个专业的思考教练，擅长用苏格拉底式追问法帮助人们深入思考。
要求：
1. 每次只问一个问题
2. 问题要层层递进，越来越深入
3. 问题要简洁明了，直击要害
4. 根据用户的回答，生成针对性的追问
5. 用中文提问

核心追问模式：
- "为什么这对你很重要？"
- "你能具体说说吗？"
- "如果...会怎样？"
- "你有没有从另一个角度想过？"
- "那背后真正想要的是什么呢？"
""",
        ThinkingStyle.COACH: """你是一位专业的 life coach，专注于帮助人们发现内心真正的渴望。
要求：
1. 倾听并理解用户的处境
2. 用开放式问题引导用户思考
3. 肯定用户的感受和思考
4. 帮助用户看到盲点
5. 用中文交流
""",
        ThinkingStyle.WHY_5: """你帮助用户通过连续追问"为什么"来找到问题的根本原因。
工作方式：
1. 用户的每个回答都追问"为什么"
2. 至少追问5层，直到找到根本原因
3. 用中文提问
4. 每轮只问一个"为什么"
""",
        ThinkingStyle.DECISION_MATRIX: """你帮助用户做决策分析。
工作方式：
1. 列出决策的所有选项
2. 分析每个选项的利弊
3. 帮助用户明确权衡标准
4. 引导用户思考"如果不选这个，最坏的结果是什么？"
5. 用中文
""",
        ThinkingStyle.PRO_CON: """你帮助用户进行利弊分析。
工作方式：
1. 系统地列出好处和坏处
2. 量化每个因素的权重
3. 问"这个好处对你来说意味着什么？"
4. 问"这个坏处最坏的结果你能接受吗？"
5. 用中文
""",
    }
    
    def __init__(
        self,
        prompt: str,
        provider: Optional[BaseLLMProvider] = None,
        use_ai: bool = True,
        show_thought: bool = True,
        max_questions: int = 10,
        session: Optional[Session] = None,
        thinking_style: ThinkingStyle = ThinkingStyle.SOCRATIC,
        stream: bool = False,
    ):
        """
        Initialize OpenThought.
        
        Args:
            prompt: The initial thought/question to explore
            provider: LLM provider instance (OpenAI, Kimi, etc.)
            use_ai: Whether to use AI for question generation
            show_thought: Whether to print thought trace
            max_questions: Maximum number of questions to ask
            session: Optional existing session to continue
            thinking_style: Thinking strategy to use
            stream: Whether to use streaming response
        """
        self.prompt = prompt
        self.provider = provider
        self.use_ai = use_ai and provider is not None
        self.show_thought = show_thought
        self.max_questions = max_questions
        self.thinking_style = thinking_style
        self.stream = stream
        
        if session:
            self.session = session
            if not self.session.initial_prompt:
                self.session.initial_prompt = prompt
        else:
            self.session = Session(initial_prompt=prompt, thinking_style=thinking_style)
        
        self.generation_count = 0
    
    @property
    def questions(self) -> List[str]:
        """Get all questions asked so far."""
        return [m.content for m in self.session.messages if m.role == "assistant"]
    
    @property
    def answers(self) -> List[str]:
        """Get all answers given so far."""
        return [m.content for m in self.session.messages if m.role == "user"]
    
    def think(self) -> str:
        """
        Generate the next question (sync version).
        
        Returns:
            A thought-provoking question
        """
        self.generation_count += 1
        
        if self.use_ai and self.provider:
            question = self._generate_ai_question()
        else:
            question = self._generate_fallback_question()
        
        self.session.add_message("assistant", question)
        return question
    
    async def athink(self) -> AsyncGenerator[str, None]:
        """
        Generate the next question (async streaming version).
        
        Yields:
            Question text chunks
        """
        if not self.use_ai or not self.provider:
            question = self._generate_fallback_question()
            yield question
            self.session.add_message("assistant", question)
            return
        
        self.generation_count += 1
        system_prompt = self.STYLE_PROMPTS.get(self.thinking_style, self.STYLE_PROMPTS[ThinkingStyle.SOCRATIC])
        
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(self.session.to_llm_messages())
        messages.append({
            "role": "user", 
            "content": "请基于以上对话，提出下一个追问。"
        })
        
        try:
            full_response = ""
            async for chunk in self.provider.astream_generate(messages, max_tokens=500):
                # Clean up the chunk
                chunk = chunk.strip()
                if chunk:
                    full_response += chunk
                    yield chunk
            
            # Ensure it ends with a question mark
            if not full_response.endswith("？") and not full_response.endswith("?"):
                yield "？"
            
            self.session.add_message("assistant", full_response + "？")
        except Exception as e:
            raise ProviderError(f"Failed to generate question: {e}")
    
    def _generate_ai_question(self) -> str:
        """Generate a contextual question using AI (sync)."""
        system_prompt = self.STYLE_PROMPTS.get(self.thinking_style, self.STYLE_PROMPTS[ThinkingStyle.SOCRATIC])
        
        messages = [
            {"role": "system", "content": system_prompt},
        ]
        messages.extend(self.session.to_llm_messages())
        messages.append({
            "role": "user", 
            "content": "请基于以上对话，提出下一个追问。"
        })
        
        try:
            response = self.provider.generate(messages, max_tokens=500)
            question = response.strip()
            if not question.endswith("？") and not question.endswith("?"):
                question += "？"
            return question
        except Exception as e:
            raise ProviderError(f"Failed to generate question: {e}")
    
    def _generate_fallback_question(self) -> str:
        """Generate a context-aware fallback question."""
        depth = len(self.questions) // 2
        question_index = len(self.questions) % len(self.DEFAULT_QUESTIONS_BY_DEPTH.get(depth, ["你能再具体说说吗？"]))
        
        questions_at_depth = self.DEFAULT_QUESTIONS_BY_DEPTH.get(depth, ["你能再具体说说吗？"])
        if question_index < len(questions_at_depth):
            return questions_at_depth[question_index]
        
        return self._generate_context_question()
    
    def _generate_context_question(self) -> str:
        """Generate a context-aware fallback question based on answers."""
        if not self.answers:
            return "你能再具体说说吗？"
        
        last_answer = self.answers[-1]
        
        # Keyword-based context detection
        keywords = {
            "钱": ["金钱对你来说代表什么？", "你赚钱的目的是什么？"],
            "自由": ["自由对你意味着什么？", "你想要什么样的自由？"],
            "成功": ["你如何定义成功？", "成功对你来说是外在成就还是内在满足？"],
            "不": ["那你真正想要的是什么呢？", "你不想这样的原因是什么？"],
            "害怕": ["你最害怕的是什么？", "这个害怕背后有什么担忧？"],
            "担心": ["你在担心什么？", "最坏的结果你能接受吗？"],
        }
        
        for key, questions in keywords.items():
            if key in last_answer:
                return questions[len(self.questions) % len(questions)]
        
        return "还有呢？或者说，你内心深处真正在追求的是什么？"
    
    def ark(self, answer: str, savepoint_name: Optional[str] = None) -> None:
        """
        Answer the current question and continue the chain.
        
        Args:
            answer: Your answer to the last question
            savepoint_name: Optional name for a savepoint before this answer
        """
        if len(self.questions) == 0:
            raise OpenThoughtError("Please call think() first to get a question.")
        
        # Create savepoint if requested
        if savepoint_name:
            self.session.add_savepoint(
                name=savepoint_name,
                question=self.questions[-1],
                answer=answer
            )
        
        self.session.add_message("user", answer)
    
    def ask(self, question: str) -> None:
        """Directly ask a question (bypassing AI generation)."""
        self.session.add_message("assistant", question)
        self.generation_count += 1
    
    def answer(self, answer: str) -> None:
        """Provide an answer (shorthand for ark)."""
        self.ark(answer)
    
    def create_branch(self, branch_name: str) -> str:
        """
        Create a new branch at current point.
        
        Returns:
            Branch savepoint ID
        """
        last_question = self.questions[-1] if self.questions else self.prompt
        return self.session.add_savepoint(
            name=branch_name,
            question=last_question,
        )
    
    def switch_branch(self, savepoint_id: str) -> int:
        """
        Switch to a different branch.
        
        Args:
            savepoint_id: The savepoint ID to switch to
        
        Returns:
            Number of messages removed
        """
        return self.session.restore_to_savepoint(savepoint_id)
    
    def print_trace(self) -> None:
        """Print the complete thought trace."""
        if not self.show_thought:
            return
        
        print("\n" + "=" * 70)
        print(f"💭 OpenThought Trace - {self.prompt}")
        print("=" * 70)
        
        user_messages = [m for m in self.session.messages if m.role == "user"]
        assistant_messages = [m for m in self.session.messages if m.role == "assistant"]
        
        for i, (q, a) in enumerate(zip(assistant_messages, user_messages), 1):
            print(f"\n❓ [Q{i}] {q.content}")
            print(f"👉 [A{i}] {a.content}")
        
        # Show savepoints
        if self.session.savepoints:
            print(f"\n💾 分支点: {len(self.session.savepoints)}")
            for sp in self.session.savepoints:
                print(f"   - {sp.name} ({sp.id})")
        
        # Unanswered questions
        if len(assistant_messages) > len(user_messages):
            unanswered = len(assistant_messages) - len(user_messages)
            print(f"\n⚠️  还有 {unanswered} 个问题等待你的回答")
        
        print("\n" + "=" * 70)
        print(f"📊 统计: {len(assistant_messages)} 个问题, {len(user_messages)} 个回答")
        print("=" * 70)
    
    def get_insights(self) -> List[str]:
        """Extract key insights from the thought process."""
        insights = []
        
        if self.answers:
            insights.append(f"🎯 你的出发点: {self.answers[0]}")
        
        depth = len(self.answers)
        if depth >= 3:
            insights.append(f"📈 你已经深入思考了 {depth} 个层次")
        
        if depth >= 5:
            insights.append("🔗 你的思考展现出了清晰的逻辑链条")
        
        if self.session.savepoints:
            insights.append(f"🌿 你创建了 {len(self.session.savepoints)} 个思考分支")
        
        if self.answers:
            last_answer = self.answers[-1]
            if len(last_answer) > 100:
                insights.append(f"💡 最新思考: {last_answer[:50]}...")
            else:
                insights.append(f"💡 最新思考: {last_answer}")
        
        return insights
    
    def export_session(self, format: str = "dict") -> Any:
        """
        Export the session in various formats.
        
        Args:
            format: Export format ("dict", "markdown", "html", "json")
        
        Returns:
            Exported data
        """
        if format == "dict":
            return self.session.to_dict()
        elif format == "markdown":
            return self.session.export_markdown()
        elif format == "html":
            return self.session.export_html()
        elif format == "json":
            import json
            return json.dumps(self.session.to_dict(), ensure_ascii=False, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def get_conversation_summary(self) -> str:
        """Get a text summary of the conversation."""
        lines = [
            f"思考主题: {self.prompt}",
            f"总计问答: {len(self.questions)} 轮",
            f"思考方式: {self.thinking_style.value}",
            "",
            "对话记录:",
        ]
        
        user_messages = [m for m in self.session.messages if m.role == "user"]
        assistant_messages = [m for m in self.session.messages if m.role == "assistant"]
        
        for i, (q, a) in enumerate(zip(assistant_messages, user_messages), 1):
            lines.append(f"\n[{i}] Q: {q.content}")
            lines.append(f"    A: {a.content}")
        
        return "\n".join(lines)
    
    def reset(self) -> None:
        """Reset the conversation (keep initial prompt)."""
        self.session.messages = []
        self.session.savepoints = []
        self.generation_count = 0
    
    def __repr__(self) -> str:
        return f"OpenThought(prompt='{self.prompt[:30]}...', questions={len(self.questions)}, style={self.thinking_style.value})"


# Convenience function for quick start
def think(prompt: str, api_key: Optional[str] = None, provider: str = "openai", **kwargs) -> OpenThought:
    """
    Quick start function for OpenThought.
    
    Args:
        prompt: The topic to think about
        api_key: API key for the LLM provider
        provider: LLM provider name
        **kwargs: Additional arguments (style, stream, etc.)
    
    Returns:
        OpenThought instance ready for thinking
    """
    from openthought.providers import create_provider
    
    llm_provider = None
    use_ai = True
    
    if api_key:
        try:
            llm_provider = create_provider(provider, api_key)
        except Exception:
            use_ai = False
    else:
        use_ai = False
    
    return OpenThought(
        prompt=prompt,
        provider=llm_provider,
        use_ai=use_ai,
        **kwargs
    )


if __name__ == "__main__":
    print("🚀 OpenThought v3.0 Demo")
    print("=" * 50)
    
    # Demo without AI
    ot = OpenThought(
        prompt="我想创业",
        use_ai=False,
        thinking_style=ThinkingStyle.SOCRATIC
    )
    
    questions_to_ask = [
        "因为我想要财务自由",
        "自由意味着不被工作束缚",
        "我想掌控自己的时间",
        "我想创造一些有价值的产品",
        "帮助更多人解决问题",
    ]
    
    print("\n📝 测试苏格拉底式追问:")
    for i, answer in enumerate(questions_to_ask):
        q = ot.think()
        print(f"\n❓ 问题 {i+1}: {q}")
        print(f"👉 回答: {answer}")
        ot.ark(answer)
    
    print("\n📊 思考洞察:")
    for insight in ot.get_insights():
        print(f"  • {insight}")
    
    print("\n🌿 测试分支功能:")
    branch_id = ot.create_branch("如果选择B方案")
    print(f"  创建分支: {branch_id}")
    ot.ark("另一个角度看这个问题")
    print(f"  当前问答轮次: {len(ot.questions)}")
    
    print("\n🔄 切换回主分支:")
    ot.switch_branch(branch_id)
    print(f"  切换后问答轮次: {len(ot.questions)}")
    
    print("\n📤 导出测试:")
    print(ot.export_session(format="markdown")[:200] + "...")
