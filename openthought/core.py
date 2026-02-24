"""
OpenThought Core Engine - Chain of Thought Implementation.
"""

import os
from typing import List, Optional

# Default questions for Socrates-style questioning
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


class OpenThought:
    """
    A Chain-of-Thought tool for deep reflection.
    
    Simulates the Socratic method to guide users through deep thinking.
    
    Example:
        >>> ot = OpenThought(prompt="I want to start a business")
        >>> ot.think()
        '什么让你想创业？'
        >>> ot.ark("Because I want to be free")
        >>> ot.think()
        '自由对你来说意味着什么？'
    """

    def __init__(
        self,
        prompt: str,
        show_thought: bool = True,
        max_questions: int = 10,
    ):
        """
        Initialize the chain-of-thought process.
        
        Args:
            prompt: The initial thought/question to explore
            show_thought: Whether to print thought trace
            max_questions: Maximum number of questions to ask
        """
        self.prompt = prompt
        self.current_thought = prompt
        self.show_thought = show_thought
        self.max_questions = max_questions
        
        self.questions: List[str] = []
        self.answers: List[str] = []
        self.trace: List[dict] = []
        self.generation_count = 0

    def think(self) -> str:
        """
        Generate the next question to guide deeper thinking.
        
        Returns:
            A thought-provoking question
        """
        question_index = len(self.questions)
        
        if question_index < len(DEFAULT_QUESTIONS):
            question = DEFAULT_QUESTIONS[question_index]
        else:
            # Generate context-aware question
            question = self._generate_context_question()
        
        self.questions.append(question)
        self.generation_count += 1
        
        # Add to trace
        self.trace.append({
            "type": "question",
            "content": question,
            "step": self.generation_count,
        })
        
        return question

    def _generate_context_question(self) -> str:
        """
        Generate a context-aware question based on previous answers.
        
        Returns:
            A personalized question
        """
        if len(self.answers) == 0:
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
            raise ValueError("Please call think() first to get a question.")
        
        self.answers.append(answer)
        self.current_thought = answer
        
        # Add to trace
        self.trace.append({
            "type": "answer",
            "content": answer,
            "step": len(self.questions),
        })

    def print_total_thought(self) -> None:
        """Print the complete thought trace."""
        if not self.show_thought:
            return
        
        print("\n" + "=" * 60)
        print(f"💭 OpenThought Trace - {self.prompt}")
        print("=" * 60)
        
        for i, (q, a) in enumerate(zip(self.questions, self.answers), 1):
            print(f"\n❓ [Q{i}] {q}")
            print(f"👉 [A{i}] {a}")
        
        # Unanswered questions
        if len(self.questions) > len(self.answers):
            unanswered = len(self.questions) - len(self.answers)
            print(f"\n⚠️  还有 {unanswered} 个问题等待你的回答")
        
        print("\n" + "=" * 60)
        print(f"📊 总计: {len(self.questions)} 个问题, {len(self.answers)} 个回答")
        print("=" * 60)

    def get_insights(self) -> List[str]:
        """
        Extract key insights from the thought process.
        
        Returns:
            List of insights extracted from the conversation
        """
        insights = []
        
        if len(self.answers) > 0:
            # First insight: Core motivation
            if self.answers:
                insights.append(f"你的出发点是: {self.answers[0]}")
            
            # Last insight: Current depth
            if len(self.answers) >= 3:
                insights.append(f"你已经深入思考了 {len(self.answers)} 个层次")
            
            # Pattern insight
            if len(self.answers) >= 5:
                insights.append("你的思考展现出了清晰的逻辑链条")
        
        return insights


if __name__ == "__main__":
    # Demo
    print("🚀 OpenThought Demo")
    print("-" * 40)
    
    ot = OpenThought(prompt="我想创业")
    
    questions_to_ask = [
        "因为我想要财务自由",
        "自由意味着不被工作束缚",
        "我想掌控自己的时间",
        "我想创造一些有价值的东西",
        "帮助更多人解决问题",
    ]
    
    for i, answer in enumerate(questions_to_ask):
        q = ot.think()
        print(f"\n❓ 问题 {i+1}: {q}")
        print(f"👉 你的回答: {answer}")
        ot.ark(answer)
    
    ot.print_total_thought()
    
    print("\n💡 洞察:")
    for insight in ot.get_insights():
        print(f"  • {insight}")
