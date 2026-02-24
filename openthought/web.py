#!/usr/bin/env python3
"""
OpenThought Web Interface - Streamlit Web App.

A beautiful web interface for AI-powered deep thinking sessions.

Run: streamlit run openthought/web.py
"""

import streamlit as st
import json
from datetime import datetime
from pathlib import Path

from openthought import OpenThought
from openthought.providers import create_provider
from openthought.storage import SessionManager, JSONStorage
from openthought.config import load_config


# Page config
st.set_page_config(
    page_title="OpenThought - 深度思考",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 20px;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    
    .question-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #667eea;
        margin: 10px 0;
    }
    
    .answer-box {
        background-color: #e8f4f8;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #00cec9;
        margin: 10px 0;
    }
    
    .insight-box {
        background-color: #fff9e6;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #fdcb6e;
        margin: 10px 0;
    }
    
    .stButton button {
        width: 100%;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize Streamlit session state."""
    if 'ot' not in st.session_state:
        st.session_state.ot = None
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'provider' not in st.session_state:
        st.session_state.provider = None
    if 'config' not in st.session_state:
        st.session_state.config = load_config()


def setup_provider():
    """Setup LLM provider based on user input."""
    provider_type = st.sidebar.selectbox(
        "选择 AI 提供商",
        ["不使用 AI (预设问题)", "OpenAI", "Kimi", "Claude", "自定义"]
    )
    
    if provider_type == "不使用 AI (预设问题)":
        return None
    
    api_key = ""
    
    if provider_type == "OpenAI":
        api_key = st.sidebar.text_input("OpenAI API Key", type="password")
        if not api_key:
            api_key = None
        provider_name = "openai"
        
    elif provider_type == "Kimi":
        api_key = st.sidebar.text_input("Kimi API Key", type="password")
        if not api_key:
            api_key = None
        provider_name = "kimi"
        
    elif provider_type == "Claude":
        api_key = st.sidebar.text_input("Claude API Key", type="password")
        if not api_key:
            api_key = None
        provider_name = "claude"
        
    elif provider_type == "自定义":
        provider_name = st.sidebar.text_input("提供商名称")
        api_key = st.sidebar.text_input("API Key", type="password")
    
    if not api_key:
        st.sidebar.warning("⚠️  未设置 API key，将使用预设问题模式")
        return None
    
    try:
        provider = create_provider(provider_name, api_key)
        return provider
    except Exception as e:
        st.sidebar.error(f"❌ 提供商连接失败: {e}")
        return None


def render_message(msg):
    """Render a single message."""
    if msg['role'] == 'assistant':
        st.markdown(f"""
        <div class="question-box">
            <b>❓ {msg['content']}</b>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="answer-box">
            <b>👉 {msg['content']}</b>
        </div>
        """, unsafe_allow_html=True)


def render_insights(insights):
    """Render insights."""
    if not insights:
        return
    
    st.markdown("### 💡 洞察")
    for insight in insights:
        st.markdown(f"""
        <div class="insight-box">
            {insight}
        </div>
        """, unsafe_allow_html=True)


def main():
    """Main app function."""
    init_session_state()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🧠 OpenThought</h1>
        <p>AI 驱动的深度思考工具 - 用苏格拉底式追问法帮助你深入思考</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("⚙️ 设置")
    
    # Setup provider
    st.session_state.provider = setup_provider()
    use_ai = st.session_state.provider is not None
    
    st.sidebar.markdown("---")
    
    # New session button
    if st.sidebar.button("🔄 新会话", use_container_width=True):
        st.session_state.ot = None
        st.session_state.messages = []
        st.session_state.running = False
        st.rerun()
    
    # Export/Import
    st.sidebar.markdown("### 💾 会话")
    
    # Session manager
    manager = SessionManager(JSONStorage())
    
    # Load session
    sessions = manager.list_all(5)
    if sessions:
        session_options = ["新会话"] + [s['id'][:8] + ": " + s['initial_prompt'][:20] for s in sessions]
        selected = st.sidebar.selectbox("加载历史会话", session_options)
        if selected != "新会话":
            session_id = selected.split(":")[0]
            data = manager.load(session_id)
            if data:
                st.session_state.ot = OpenThought(
                    prompt=data['initial_prompt'],
                    provider=st.session_state.provider,
                    use_ai=use_ai,
                )
                st.session_state.messages = data.get('messages', [])
    
    # Main content
    if st.session_state.ot is None:
        # New session setup
        st.markdown("### 💭 开始新的思考")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            prompt = st.text_input("你想思考什么？", placeholder="例如：我想创业...")
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            start_btn = st.button("🚀 开始思考", type="primary")
        
        if start_btn and prompt:
            st.session_state.ot = OpenThought(
                prompt=prompt,
                provider=st.session_state.provider,
                use_ai=use_ai,
            )
            st.session_state.messages = []
            
            # Get first question
            question = st.session_state.ot.think()
            st.session_state.messages.append({
                'role': 'assistant',
                'content': question,
                'timestamp': datetime.now().isoformat()
            })
            
            st.rerun()
    
    else:
        # Active session
        st.markdown(f"### 🎯 思考主题: {st.session_state.ot.prompt}")
        
        # Display messages
        for msg in st.session_state.messages:
            render_message(msg)
        
        st.markdown("### ✍️ 你的回答")
        
        # Answer input
        answer = st.text_area("在这里输入你的回答...", height=100)
        
        col1, col2 = st.columns(2)
        
        with col1:
            submit_btn = st.button("📤 提交回答", type="primary")
        
        with col2:
            skip_btn = st.button("⏭️ 跳过")
        
        if submit_btn and answer:
            st.session_state.messages.append({
                'role': 'user',
                'content': answer,
                'timestamp': datetime.now().isoformat()
            })
            
            st.session_state.ot.ark(answer)
            
            # Get next question
            question = st.session_state.ot.think()
            st.session_state.messages.append({
                'role': 'assistant',
                'content': question,
                'timestamp': datetime.now().isoformat()
            })
            
            st.rerun()
        
        if skip_btn:
            # Skip without answering
            st.session_state.messages.append({
                'role': 'user',
                'content': "[跳过]",
                'timestamp': datetime.now().isoformat()
            })
            
            st.session_state.ot.ark("[跳过]")
            
            question = st.session_state.ot.think()
            st.session_state.messages.append({
                'role': 'assistant',
                'content': question,
                'timestamp': datetime.now().isoformat()
            })
            
            st.rerun()
        
        # Insights
        insights = st.session_state.ot.get_insights()
        if insights:
            render_insights(insights)
        
        # Save session
        if st.button("💾 保存这个会话"):
            session_id = manager.save(st.session_state.ot)
            st.success(f"✅ 会话已保存: {session_id}")
        
        # Export
        if st.button("📤 导出对话"):
            summary = st.session_state.ot.get_conversation_summary()
            st.download_button(
                "下载对话记录",
                summary,
                "openthought_conversation.txt",
                "text/plain"
            )


if __name__ == "__main__":
    main()
