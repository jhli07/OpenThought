"""
OpenThought CLI - Interactive Command Line Interface.

A rich, colorful terminal experience for deep thinking sessions.
"""

import os
import sys
from typing import Optional
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.table import Table
from rich import box
from rich.align import Align

from openthought.core import OpenThought, Session
from openthought.providers import create_provider
from openthought.config import load_config
from openthought.storage import SessionManager, JSONStorage

console = Console()


def print_banner():
    """Print the OpenThought banner."""
    banner = r"""
    ╔═══════════════════════════════════════════════════════╗
    ║                                                       ║
    ║   ██████╗ ██████╗  ██████╗  █████╗ ██╗     ██╗     ║
    ║  ██╔════╝ ██╔══██╗██╔═══██╗██╔══██╗██║     ██║     ║
    ║  ██║  ███╗██████╔╝██║   ██║███████║██║     ██║     ║
    ║  ██║   ██║██╔══██╗██║   ██║██╔══██║██║     ██║     ║
    ║  ╚██████╔╝██║  ██║╚██████╔╝██║  ██║███████╗███████╗║
    ║   ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝╚══════╝║
    ║                                                       ║
    ║         深度思考的链式引导工具 v2.0                    ║
    ║     AI-Powered Chain-of-Thought Tool                  ║
    ║                                                       ║
    ╚═══════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold blue")


def print_welcome():
    """Print welcome message."""
    console.print("\n🌟 欢迎使用 OpenThought v2.0！", style="bold green")
    console.print("我会用苏格拉底式追问法 + AI 智能分析，帮助你深度思考任何问题。\n")
    console.print("💡 提示:", style="bold yellow")
    console.print("  • 输入你的想法，我会追问")
    console.print("  • 直接回车跳过回答")
    console.print("  • 输入 /save 保存对话")
    console.print("  • 输入 /history 查看历史")
    console.print("  • 输入 /insights 查看洞察")
    console.print("  • 输入 /quit 退出\n")


def get_api_key(provider: str) -> Optional[str]:
    """Get API key from environment or prompt."""
    env_keys = {
        "openai": "OPENAI_API_KEY",
        "kimi": "KIMI_API_KEY",
        "moonshot": "KIMI_API_KEY",
        "claude": "ANTHROPIC_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
    }
    
    env_key = env_keys.get(provider)
    if env_key and os.environ.get(env_key):
        return os.environ[env_key]
    
    return None


def setup_provider(config) -> Optional:
    """Setup LLM provider based on config."""
    if not config.use_ai:
        return None
    
    provider_name = config.llm.provider
    api_key = config.llm.api_key or get_api_key(provider_name)
    
    if not api_key:
        console.print("⚠️  未找到 API 键，将使用预设问题模式（无 AI）", style="yellow")
        console.print("   设置环境变量:", style="dim")
        console.print(f"   • OpenAI: export OPENAI_API_KEY=sk-...", style="dim")
        console.print(f"   • Kimi: export KIMI_API_KEY=...", style="dim")
        console.print(f"   • Claude: export ANTHROPIC_API_KEY=sk-ant-...", style="dim")
        return None
    
    try:
        provider = create_provider(
            name=provider_name,
            api_key=api_key,
            model=config.llm.model or None,
        )
        console.print(f"✅ 已连接 AI: {provider.provider_name} ({provider.get_model_name()})", style="green")
        return provider
    except Exception as e:
        console.print(f"⚠️  AI 连接失败: {e}", style="yellow")
        console.print("   将使用预设问题模式", style="dim")
        return None


def run_interactive():
    """Run interactive thinking session."""
    print_banner()
    print_welcome()
    
    # Load config
    config = load_config()
    
    # Setup provider
    provider = setup_provider(config)
    
    # Setup storage
    storage = JSONStorage()
    manager = SessionManager(storage)
    
    # Get initial prompt
    prompt = Prompt.ask("💭 你想思考什么？", default="我为什么存在？")
    
    if not prompt.strip():
        prompt = "我为什么存在？"
    
    # Initialize OpenThought
    ot = OpenThought(
        prompt=prompt,
        provider=provider,
        use_ai=provider is not None,
        show_thought=config.show_thought,
        max_questions=config.max_questions,
    )
    
    console.print(f"\n🚀 开始思考：{prompt}", style="bold cyan")
    
    command_help = "\n命令: /save=保存 /history=历史 /insights=洞察 /quit=退出"
    console.print(command_help, style="dim")
    
    try:
        while True:
            # Check if we've asked enough questions
            if len(ot.questions) >= ot.max_questions:
                console.print("\n⚠️  已达到最大问题数", style="yellow")
                break
            
            # Get next question
            question = ot.think()
            
            # Print question with style
            panel = Panel(
                Align(Text(question, justify="center", style="bold yellow"), align="center"),
                title=f"❓ 思考问题 #{len(ot.questions)}",
                border_style="blue",
                box=box.ROUNDED,
            )
            console.print(panel)
            
            # Get answer
            answer = Prompt.ask("👉 你的回答", default="", show_default=False).strip()
            
            if not answer:
                # Skip with empty input
                console.print("   [跳过回答]\n", style="dim")
                continue
            
            ot.ark(answer)
            console.print("")  # Empty line
            
            # Handle commands
            if answer.startswith("/"):
                command = answer.lower().strip()
                
                if command == "/quit" or command == "/q":
                    break
                
                elif command == "/save" or command == "/s":
                    session_id = manager.save(ot)
                    console.print(f"✅ 对话已保存: {session_id}", style="green")
                
                elif command == "/history" or command == "/h":
                    sessions = manager.list_all(5)
                    if sessions:
                        table = Table(title="💾 历史会话", show_header=True)
                        table.add_column("ID", style="dim")
                        table.add_column("主题", style="cyan")
                        table.add_column("更新于", style="dim")
                        for s in sessions:
                            table.add_row(s["id"], s["initial_prompt"][:30], s["updated_at"][:10])
                        console.print(table)
                    else:
                        console.print("暂无历史会话", style="dim")
                
                elif command == "/insights" or command == "/i":
                    insights = ot.get_insights()
                    if insights:
                        console.print("\n💡 思考洞察:", style="bold green")
                        for insight in insights:
                            console.print(f"  • {insight}")
                    else:
                        console.print("继续思考以获取洞察...", style="dim")
                
                elif command == "/help":
                    console.print(command_help, style="dim")
                
                else:
                    console.print(f"未知命令: {command}", style="red")
                    console.print(command_help, style="dim")
    
    except KeyboardInterrupt:
        console.print("\n\n👋 收到退出信号")
    
    # Final summary
    console.print("\n" + "=" * 60)
    console.print("📊 本次思考总结", style="bold")
    console.print("=" * 60)
    
    ot.print_trace()
    
    # Final insights
    insights = ot.get_insights()
    if insights:
        console.print("\n💡 本次洞察:", style="bold green")
        for insight in insights:
            console.print(f"  • {insight}")
    
    # Ask to save
    if Prompt.ask("\n💾 保存这次思考？", choices=["y", "n"], default="y") == "y":
        session_id = manager.save(ot)
        console.print(f"✅ 已保存到历史: {session_id}", style="green")
        console.print(f"📁 查看历史: openthought --history", style="dim")
    
    console.print("\n👋 感谢使用 OpenThought！下次见！", style="bold cyan")


def show_history(limit: int = 10):
    """Show session history."""
    storage = JSONStorage()
    manager = SessionManager(storage)
    
    sessions = manager.list_all(limit)
    
    if not sessions:
        console.print("暂无历史会话", style="yellow")
        return
    
    table = Table(title="💾 历史思考记录", show_header=True)
    table.add_column("ID", style="dim", width=12)
    table.add_column("主题", style="cyan")
    table.add_column("轮次", justify="right")
    table.add_column("创建时间", style="dim")
    table.add_column("更新时间", style="dim")
    
    for s in sessions:
        msg_count = len(s.get("messages", []))
        table.add_row(
            s["id"],
            s["initial_prompt"][:40],
            str(msg_count // 2),  # Q&A pairs
            s["created_at"][:10],
            s["updated_at"][:10],
        )
    
    console.print(table)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="OpenThought - AI-Powered Chain-of-Thought Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "prompt",
        nargs="?",
        default=None,
        help="Initial prompt to think about",
    )
    
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Force interactive mode",
    )
    
    parser.add_argument(
        "--history", "-H",
        action="store_true",
        help="Show session history",
    )
    
    parser.add_argument(
        "--provider", "-p",
        default="openai",
        choices=["openai", "kimi", "claude"],
        help="LLM provider to use",
    )
    
    parser.add_argument(
        "--no-ai",
        action="store_true",
        help="Disable AI, use preset questions only",
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode",
    )
    
    args = parser.parse_args()
    
    # Show history if requested
    if args.history:
        show_history()
        return
    
    # Interactive mode
    if args.prompt is None or args.interactive:
        run_interactive()
        return
    
    # Single prompt mode
    print_banner()
    
    config = load_config()
    if args.debug:
        config.debug = True
    
    # Setup provider
    provider = None
    if not args.no_ai:
        api_key = get_api_key(args.provider)
        if api_key:
            try:
                provider = create_provider(args.provider, api_key)
                console.print(f"✅ 已连接: {args.provider}")
            except Exception as e:
                console.print(f"⚠️  连接失败: {e}")
    
    # Run single prompt
    ot = OpenThought(
        prompt=args.prompt,
        provider=provider,
        use_ai=provider is not None,
        show_thought=True,
    )
    
    console.print(f"\n🚀 开始思考: {args.prompt}\n")
    
    # Auto-generate a few questions
    for _ in range(3):
        q = ot.think()
        console.print(f"❓ {q}")
        ot.ark("[自动跳过]")
    
    ot.print_trace()
    
    insights = ot.get_insights()
    if insights:
        console.print("\n💡 洞察:")
        for i in insights:
            console.print(f"  • {i}")


if __name__ == "__main__":
    main()
