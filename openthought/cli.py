"""
OpenThought CLI - Command Line Interface.
"""

import sys
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from openthought.core import OpenThought

console = Console()


def print_welcome():
    """Print welcome message."""
    welcome_text = """
    ╔═══════════════════════════════════════════════════════╗
    ║                                                       ║
    ║   ██████╗ ██████╗  ██████╗  █████╗ ██╗     ██╗     ║
    ║  ██╔════╝ ██╔══██╗██╔═══██╗██╔══██╗██║     ██║     ║
    ║  ██║  ███╗██████╔╝██║   ██║███████║██║     ██║     ║
    ║  ██║   ██║██╔══██╗██║   ██║██╔══██║██║     ██║     ║
    ║  ╚██████╔╝██║  ██║╚██████╔╝██║  ██║███████╗███████╗║
    ║   ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝╚══════╝║
    ║                                                       ║
    ║         深度思考的链式引导工具                         ║
    ║     Chain-of-Thought Tool for Deep Reflection         ║
    ║                                                       ║
    ╚═══════════════════════════════════════════════════════╝
    """
    console.print(welcome_text, style="bold blue")


def run_interactive():
    """Run interactive thought session."""
    print_welcome()
    
    console.print("\n🌟 欢迎使用 OpenThought！", style="bold green")
    console.print("我会用苏格拉底式追问法，帮助你深度思考任何问题。\n")
    
    # Get initial prompt
    prompt = console.input("💭 [bold]你想思考什么？[/bold] ").strip()
    
    if not prompt:
        console.print("❌ 请输入一个问题或想法", style="red")
        return
    
    # Initialize
    ot = OpenThought(prompt=prompt)
    
    console.print(f"\n🚀 开始思考：{prompt}", style="bold cyan")
    console.print("按 Ctrl+C 随时退出\n")
    
    try:
        while True:
            question = ot.think()
            
            # Print question with style
            panel = Panel(
                Text(question, justify="center", style="bold yellow"),
                title=f"❓ 思考问题 #{len(ot.questions)}",
                border_style="blue",
            )
            console.print(panel)
            
            # Get answer
            answer = console.input("👉 你的回答 (直接回车跳过): ").strip()
            
            if answer:
                ot.ark(answer)
            else:
                ot.ark("[跳过]")
            
            console.print("")  # Empty line
    
    except KeyboardInterrupt:
        console.print("\n\n👋 思考结束！")
        ot.print_total_thought()
        
        # Show insights
        insights = ot.get_insights()
        if insights:
            console.print("\n💡 你的思考洞察：", style="bold green")
            for insight in insights:
                console.print(f"  • {insight}")


def main():
    """Main entry point."""
    run_interactive()


if __name__ == "__main__":
    main()
