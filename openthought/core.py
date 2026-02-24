"""
OpenThought Core Engine - AI-Powered Chain-of-Thought Implementation.

This module provides the core functionality for AI-guided deep thinking
using the Socratic method.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable
from dataclasses import dataclass, field, asdict


class OpenThoughtError(Exception):
    """Base exception for OpenThought."""
    pass


class ConfigurationError(OpenThoughtError):
    """Raised when configuration is invalid."""
    pass


class ProviderError(OpenThoughtError):
    """Raised when LLM provider fails."""
    pass


@dataclass
class Message:
    """A single message in the conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        return cls(**data)


@dataclass
class Session:
    """
    A thinking session that persists across conversations.
    
    Attributes:
        id: Unique session identifier
        initial_prompt: The original question/topic
        messages: List of conversation messages
        created_at: Session creation timestamp
        updated_at: Last update timestamp
        metadata: Optional additional metadata
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    initial_prompt: str = ""
    messages: List[Message] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to the session."""
        self.messages.append(Message(role=role, content=content))
        self.updated_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "initial_prompt": self.initial_prompt,
            "messages": [m.to_dict() for m in self.messages],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        messages = [Message.from_dict(m) for m in data.get("messages", [])]
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            initial_prompt=data.get("initial_prompt", ""),
            messages=messages,
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            metadata=data.get("metadata", {}),
        )
    
    def to_llm_messages(self) -> List[Dict[str, str]]:
        """Convert to LLM message format."""
        messages = []
        if self.initial_prompt:
            messages.append({"role": "system", "content": f"用户想要思考的主题: {self.initial_prompt}"})
        messages.extend([{"role": m.role, "content": m.content} for m in self.messages])
        return messages


@runtime_checkable
class BaseLLMProvider(Protocol):
    """Protocol for LLM providers."""
    
    def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Generate a response from the LLM."""
        ...
    
    def get_model_name(self) -> str:
        """Get the model name."""
        ...


class OpenThought:
    """
    AI-Powered Chain-of-Thought Tool for Deep Reflection.
    
    Simulates the Socratic method with AI to guide users through
    deep, meaningful thinking sessions.
    
    Example:
        >>> ot = OpenThought(prompt="我想创业")
        >>> question = ot.think()
        >>> print(question)
        '什么让你想创业？'
        >>> ot.ark("因为我想赚钱")
        >>> question = ot.think()
        >>> print(question)
        '金钱对你来说意味着什么？'
    """
    
    VERSION = "2.0.0"
    
    # Default Socratic questions (fallback when AI is unavailable)
    DEFAULT_QUESTIONS = [
        "什么让你想到这个？",
        "你能具体说说吗？",
        "为什么这对你很重要？",
        "如果实现这个，你的感受会怎样？",
        "你觉得最大的挑战是什么？",
        "你有没有从另一个角度想过这个问题？",
        "如果你的朋友遇到同样的问题，你会怎么建议他？",
        "一年后的你，会怎么看今天的这个问题？",
        "你有没有忽略什么重要的因素？",
        "最终，你想要达成的是什么？",
    ]
    
    def __init__(
        self,
        prompt: str,
        provider: Optional[BaseLLMProvider] = None,
        use_ai: bool = True,
        show_thought: bool = True,
        max_questions: int = 10,
        session: Optional[Session] = None,
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
        """
        self.prompt = prompt
        self.provider = provider
        self.use_ai = use_ai and provider is not None
        self.show_thought = show_thought
        self.max_questions = max_questions
        
        if session:
            self.session = session
            if not self.session.initial_prompt:
                self.session.initial_prompt = prompt
        else:
            self.session = Session(initial_prompt=prompt)
        
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
        Generate the next question to guide deeper thinking.
        
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
    
    def _generate_ai_question(self) -> str:
        """Generate a contextual question using AI."""
        system_prompt = """你是一个专业的思考教练，擅长用苏格拉底式追问法帮助人们深入思考。

你的任务是针对用户给出的主题，通过提问引导他们深入思考。

要求：
1. 每次只问一个问题
2. 问题要层层递进，越来越深入
3. 问题要简洁明了，直击要害
4. 不要重复已经问过的问题
5. 根据用户的回答，生成针对性的追问
6. 用中文提问

苏格拉底式追问的核心是：
- "为什么这对你很重要？"
- "你能具体说说吗？"
- "如果...会怎样？"
- "你有没有从另一个角度想过？"
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
        ]
        
        # Add conversation history
        messages.extend(self.session.to_llm_messages())
        
        # Add final prompt
        messages.append({
            "role": "user", 
            "content": "请基于以上对话，提出下一个追问。用户刚刚回答了上一个问题，请针对他的回答继续深入追问。回复只需要输出问题本身，不要其他内容。"
        })
        
        try:
            response = self.provider.generate(messages, max_tokens=500)
            question = response.strip()
            # Ensure it ends with a question mark
            if not question.endswith("？") and not question.endswith("?"):
                question += "？"
            return question
        except Exception as e:
            raise ProviderError(f"Failed to generate question: {e}")
    
    def _generate_fallback_question(self) -> str:
        """Generate a question using predefined templates."""
        question_index = len(self.questions)
        
        if question_index < len(self.DEFAULT_QUESTIONS):
            return self.DEFAULT_QUESTIONS[question_index]
        
        # Context-aware fallback
        return self._generate_context_question()
    
    def _generate_context_question(self) -> str:
        """Generate a context-aware fallback question."""
        if not self.answers:
            return "你能再具体说说吗？"
        
        last_answer = self.answers[-1]
        
        if "不" in last_answer or "没有" in last_answer:
            return "那你真正想要的是什么呢？"
        
        if "钱" in last_answer or "赚钱" in last_answer:
            return "金钱对你来说代表什么？"
        
        if "自由" in last_answer:
            return "自由对你意味着什么？是你想要的生活方式吗？"
        
        if "成功" in last_answer:
            return "你如何定义成功？是外在成就还是内在满足？"
        
        return "还有呢？或者说，你内心深处真正在追求的是什么？"
    
    def ark(self, answer: str) -> None:
        """
        Answer the current question and continue the chain.
        
        Args:
            answer: Your answer to the last question
        """
        if len(self.questions) == 0:
            raise OpenThoughtError("Please call think() first to get a question.")
        
        self.session.add_message("user", answer)
    
    def ask(self, question: str) -> None:
        """
        Directly ask a question (bypassing AI generation).
        
        Args:
            question: The question to ask
        """
        self.session.add_message("assistant", question)
        self.generation_count += 1
    
    def answer(self, answer: str) -> None:
        """
        Provide an answer (shorthand for ark).
        
        Args:
            answer: Your answer
        """
        self.ark(answer)
    
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
        
        # Unanswered questions
        if len(assistant_messages) > len(user_messages):
            unanswered = len(assistant_messages) - len(user_messages)
            print(f"\n⚠️  还有 {unanswered} 个问题等待你的回答")
        
        print("\n" + "=" * 70)
        print(f"📊 统计: {len(assistant_messages)} 个问题, {len(user_messages)} 个回答")
        print("=" * 70)
    
    def get_insights(self) -> List[str]:
        """
        Extract key insights from the thought process.
        
        Returns:
            List of insights
        """
        insights = []
        
        if self.answers:
            # Core motivation
            insights.append(f"🎯 你的出发点: {self.answers[0]}")
        
        # Depth analysis
        if len(self.answers) >= 3:
            insights.append(f"📈 你已经深入思考了 {len(self.answers)} 个层次")
        
        if len(self.answers) >= 5:
            insights.append("🔗 你的思考展现出了清晰的逻辑链条")
        
        # Latest insight
        if self.answers:
            insights.append(f"💡 最新思考: {self.answers[-1][:50]}..." if len(self.answers[-1]) > 50 else f"💡 最新思考: {self.answers[-1]}")
        
        return insights
    
    def export_session(self) -> Dict[str, Any]:
        """Export the session as a dictionary."""
        return self.session.to_dict()
    
    def get_conversation_summary(self) -> str:
        """Get a text summary of the conversation."""
        lines = [
            f"思考主题: {self.prompt}",
            f"总计问答: {len(self.questions)} 轮",
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
        self.generation_count = 0
    
    def __repr__(self) -> str:
        return f"OpenThought(prompt='{self.prompt[:30]}...', questions={len(self.questions)})"


# Convenience function for quick start
def think(prompt: str, api_key: Optional[str] = None, provider: str = "openai") -> OpenThought:
    """
    Quick start function for OpenThought.
    
    Args:
        prompt: The topic to think about
        api_key: API key for the LLM provider
        provider: LLM provider name ("openai", "kimi", "claude")
    
    Returns:
        OpenThought instance ready for thinking
    
    Example:
        >>> ot = think("我想创业")
        >>> print(ot.think())
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
    
    return OpenThought(prompt=prompt, provider=llm_provider, use_ai=use_ai)


if __name__ == "__main__":
    print("🚀 OpenThought v2.0 Demo")
    print("=" * 50)
    
    # Demo without AI
    ot = OpenThought(prompt="我想创业", use_ai=False)
    
    questions_to_ask = [
        "因为我想要财务自由",
        "自由意味着不被工作束缚",
        "我想掌控自己的时间",
        "我想创造一些有价值的产品",
        "帮助更多人解决问题",
    ]
    
    for i, answer in enumerate(questions_to_ask):
        q = ot.think()
        print(f"\n❓ 问题 {i+1}: {q}")
        print(f"👉 你的回答: {answer}")
        ot.ark(answer)
    
    ot.print_trace()
    
    print("\n💡 洞察:")
    for insight in ot.get_insights():
        print(f"  • {insight}")
    
    print("\n📄 对话摘要:")
    print(ot.get_conversation_summary())
