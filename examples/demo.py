#!/usr/bin/env python3
"""
OpenThought Demo - 示例代码
"""

from openthought import OpenThought


def demo_basic():
    """Basic usage demo."""
    print("🎯 OpenThought 基础使用示例\n")
    print("=" * 50)
    
    # 初始化
    ot = OpenThought(prompt="我想创业")
    
    # 预设问答
    q1 = ot.think()
    print(f"Q1: {q1}")
    ot.ark("因为我想赚钱")
    
    q2 = ot.think()
    print(f"\nQ2: {q2}")
    ot.ark("赚钱意味着自由")
    
    q3 = ot.think()
    print(f"\nQ3: {q3}")
    ot.ark("自由意味着可以掌控自己的时间")
    
    q4 = ot.think()
    print(f"\nQ4: {q4}")
    ot.ark("我想创造一些有价值的产品")
    
    # 打印完整思考轨迹
    ot.print_total_thought()
    
    # 洞察
    print("\n💡 洞察:")
    for insight in ot.get_insights():
        print(f"  • {insight}")


def demo_custom():
    """Custom prompt demo."""
    print("\n\n🎯 自定义主题示例\n")
    print("=" * 50)
    
    ot = OpenThought(prompt="我想转行做程序员")
    
    questions = [
        "因为我觉得编程很有意思",
        "有意思具体指什么？",
        "我想创造产品帮助别人",
    ]
    
    for i, answer in enumerate(questions):
        q = ot.think()
        print(f"\nQ{i+1}: {q}")
        print(f"A{i+1}: {answer}")
        ot.ark(answer)
    
    ot.print_total_thought()


if __name__ == "__main__":
    demo_basic()
    demo_custom()
