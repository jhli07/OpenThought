#!/usr/bin/env python3
"""
OpenThought Demo Scripts - Showcasing various use cases.

Run: python examples/demo.py
"""

from openthought import OpenThought, think
from openthought.providers import create_provider
from openthought.storage import SessionManager, JSONStorage


def demo_basic_usage():
    """Basic usage without AI."""
    print("\n" + "=" * 60)
    print("🎯 Demo 1: 基础使用（无 AI）")
    print("=" * 60)
    
    ot = OpenThought(prompt="我想创业")
    
    questions = [
        "因为我想要财务自由",
        "自由意味着不被工作束缚",
        "我想掌控自己的时间",
    ]
    
    for i, answer in enumerate(questions):
        q = ot.think()
        print(f"\n❓ 问题 {i+1}: {q}")
        print(f"👉 你的回答: {answer}")
        ot.ark(answer)
    
    ot.print_trace()
    
    print("\n💡 洞察:")
    for insight in ot.get_insights():
        print(f"  • {insight}")


def demo_with_api_key():
    """Usage with AI API key."""
    print("\n" + "=" * 60)
    print("🤖 Demo 2: 使用 AI API")
    print("=" * 60)
    print("提示: 设置环境变量 OPENAI_API_KEY 或 KIMI_API_KEY")
    print("-" * 60)
    
    # Try to create provider
    api_key = None
    provider_name = "openai"
    
    import os
    if os.environ.get("OPENAI_API_KEY"):
        api_key = os.environ["OPENAI_API_KEY"]
        provider_name = "openai"
    elif os.environ.get("KIMI_API_KEY"):
        api_key = os.environ["KIMI_API_KEY"]
        provider_name = "kimi"
    elif os.environ.get("ANTHROPIC_API_KEY"):
        api_key = os.environ["ANTHROPIC_API_KEY"]
        provider_name = "claude"
    
    if not api_key:
        print("⚠️  未找到 API key，使用预设问题模式")
        return demo_basic_usage()
    
    try:
        provider = create_provider(provider_name, api_key)
        print(f"✅ 已连接: {provider_name}")
        
        ot = OpenThought(prompt="我该学编程吗？", provider=provider)
        
        # Just show one question
        q = ot.think()
        print(f"\n❓ AI 生成的问题: {q}")
        ot.ark("因为我想转行")
        
        # Get trace
        ot.print_trace()
        
    except Exception as e:
        print(f"❌ API 错误: {e}")


def demo_session_management():
    """Session persistence demo."""
    print("\n" + "=" * 60)
    print("💾 Demo 3: 会话管理")
    print("=" * 60)
    
    # Use temp storage
    from pathlib import Path
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = JSONStorage(tmpdir)
        manager = SessionManager(storage)
        
        # Create and save a session
        ot = OpenThought(prompt="人生的意义是什么？")
        ot.think()
        ot.ark("寻找快乐")
        ot.think()
        ot.ark("帮助他人")
        
        # Save
        session_id = manager.save(ot)
        print(f"✅ 会话已保存: {session_id}")
        
        # List all sessions
        print("\n📋 所有会话:")
        for s in manager.list_all():
            print(f"  • {s['id']}: {s['initial_prompt']}")
        
        # Load back
        print(f"\n🔄 加载会话: {session_id}")
        loaded_data = manager.load(session_id)
        print(f"  主题: {loaded_data['initial_prompt']}")
        print(f"  消息数: {len(loaded_data['messages'])}")


def demo_thinking_scenarios():
    """Different thinking scenarios."""
    print("\n" + "=" * 60)
    print("🎭 Demo 4: 多种思考场景")
    print("=" * 60)
    
    scenarios = [
        {
            "prompt": "我想买房",
            "context": "在考虑是否要买人生第一套房",
        },
        {
            "prompt": "该不该分手",
            "context": "感情问题需要理性思考",
        },
        {
            "prompt": "职业选择",
            "context": "在大厂和创业公司之间犹豫",
        },
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n场景 {i}: {scenario['context']}")
        print(f"主题: {scenario['prompt']}")
        
        ot = OpenThought(prompt=scenario['prompt'], use_ai=False)
        ot.think()
        ot.ark("[示例回答]")
        ot.think()
        ot.ark("[示例回答]")
        
        insights = ot.get_insights()
        print(f"洞察: {len(insights)} 条")


def demo_exports():
    """Export capabilities demo."""
    print("\n" + "=" * 60)
    print("📤 Demo 5: 导出功能")
    print("=" * 60)
    
    ot = OpenThought(prompt="我想写一本书")
    ot.think()
    ot.ark("分享我的经验")
    ot.think()
    ot.ark("帮助更多人成长")
    
    # Export as dict
    data = ot.export_session()
    print("✅ 导出为字典:", type(data))
    print(f"  keys: {list(data.keys())}")
    
    # Export as text summary
    summary = ot.get_conversation_summary()
    print("\n📝 对话摘要:")
    print("-" * 40)
    print(summary[:500] + "..." if len(summary) > 500 else summary)


def demo_quick_start():
    """Quick start function demo."""
    print("\n" + "=" * 60)
    print("⚡ Demo 6: 快速启动")
    print("=" * 60)
    print("使用 think() 函数快速开始思考")
    print("-" * 60)
    
    # This will use preset questions without API key
    ot = think("我想学画画")
    print(f"✅ 创建成功: {ot}")
    print(f"提问: {ot.think()}")
    ot.ark("因为画画让我开心")


def main():
    """Run all demos."""
    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║                                                       ║
    ║           OpenThought v2.0 使用示例                    ║
    ║           AI-Powered Chain-of-Thought Tool            ║
    ║                                                       ║
    ╚═══════════════════════════════════════════════════════╝
    """)
    
    # Demo 1: Basic usage
    demo_basic_usage()
    
    input("\n按回车继续下一个示例...")
    
    # Demo 2: With API
    demo_with_api_key()
    
    input("\n按回车继续下一个示例...")
    
    # Demo 3: Session management
    demo_session_management()
    
    input("\n按回车继续下一个示例...")
    
    # Demo 4: Different scenarios
    demo_thinking_scenarios()
    
    input("\n按回车继续下一个示例...")
    
    # Demo 5: Exports
    demo_exports()
    
    input("\n按回车继续下一个示例...")
    
    # Demo 6: Quick start
    demo_quick_start()
    
    print("\n" + "=" * 60)
    print("🎉 所有示例完成！")
    print("=" * 60)
    print("\n📚 了解更多:")
    print("  • GitHub: https://github.com/jhli07/OpenThought")
    print("  • 文档: https://github.com/jhli07/OpenThought#readme")
    print("  • 问题反馈: https://github.com/jhli07/OpenThought/issues")


if __name__ == "__main__":
    main()
