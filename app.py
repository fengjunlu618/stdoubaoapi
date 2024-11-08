import streamlit as st
import requests
import json
import time
from dotenv import load_dotenv
import os

# 加载.env文件
load_dotenv()

# 设置页面配置
st.set_page_config(
    page_title="Grok AI 聊天机器人",
    page_icon="🤖"
)

# 从环境变量获取API密钥
api_key = os.getenv("XAIAPI_KEY")

# 如果API密钥未设置，显示输入框让用户输入
if not api_key:
    api_key = st.text_input("请输入您的 X.AI API Key:", type="password")
    if not api_key:
        st.warning("请��.env文件中设置XAIAPI_KEY或在上方输入框中输入您的API Key")
        st.stop()

# 初始化会话状态
if "messages" not in st.session_state:
    st.session_state.messages = []

def call_xai_api_stream(prompt):
    url = "https://api.x.ai/v1/chat/completions"
    
    # 构建消息历史
    messages = [
        {
            "role": "system",
            "content": "You are Grok, a chatbot inspired by the Hitchhikers Guide to the Galaxy."
        }
    ]
    
    # 添加历史对话
    for message in st.session_state.messages:
        messages.append({"role": message["role"], "content": message["content"]})
    
    # 添加当前问题
    messages.append({"role": "user", "content": prompt})

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",  # 使用环境变量中的api_key
        "Accept": "text/event-stream"
    }

    payload = {
        "messages": messages,
        "model": "grok-beta",
        "stream": True,
        "temperature": 0.7
    }

    try:
        response = requests.post(url, headers=headers, json=payload, stream=True)
        response.raise_for_status()
        
        # 创建占位符用于流式输出
        placeholder = st.empty()
        response_text = ""

        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = line[6:]
                    if data == '[DONE]':
                        break
                    try:
                        chunk = json.loads(data)
                        if chunk.get('choices') and chunk['choices'][0].get('delta', {}).get('content'):
                            content = chunk['choices'][0]['delta']['content']
                            response_text += content
                            # 更新显示的响应
                            placeholder.markdown(response_text)
                    except json.JSONDecodeError:
                        continue
        
        return response_text

    except requests.exceptions.RequestException as e:
        st.error(f"API调用错误: {e}")
        return None

# 页面标题
st.title("🤖 Grok AI 聊天机器人")
st.markdown("""
👋 欢迎使用Grok AI聊天机器人！  
👨‍💻 By 逢君  
💡 这是一个基于x.ai API的聊天机器人，灵感来自《银河系漫游指南》。  
✨ 支持流式输出，实时显示回答。
""")

# 显示聊天历史
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 用户输入
if prompt := st.chat_input("在这里输入您的问题..."):
    # 显示用户消息
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 将用户消息添加到历史记录
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 显示助手消息
    with st.chat_message("assistant"):
        response = call_xai_api_stream(prompt)
        if response:
            # 将助手响应添加到历史记录
            st.session_state.messages.append({"role": "assistant", "content": response})

# 添加清除按钮
if st.button("🗑️ 清除对话历史"):
    st.session_state.messages = []
    st.rerun()

# 页脚
st.markdown("---")
st.markdown("<div style='text-align: center'>Powered by x.ai API | 仅供学习交流使用</div>", unsafe_allow_html=True) 