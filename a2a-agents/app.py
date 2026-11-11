import streamlit as st
import requests
import time

st.set_page_config(page_title="E-Commerce AI Agents", page_icon="🛒", layout="wide")

st.title("🛒 Multi-Agent E-Commerce System")
st.caption("Powered by MCP + A2A protocols | Local Qwen2.5 LLM")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            # Show routing info
            if "routing_display" in message:
                st.info(f"🧭 {message['routing_display']}")
            if message.get("tools_called"):
                st.code(f"🔧 Tools called: {', '.join(message['tools_called'])}", language=None)
            st.markdown(message["content"])
            if "latency_ms" in message:
                st.caption(f"⏱️ {message['latency_ms']:.0f}ms | trace: {message['trace_id']}")
        else:
            st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask about orders, inventory, or cart..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get response from API
    with st.chat_message("assistant"):
        with st.spinner("🤔 Agents are thinking..."):
            try:
                response = requests.post(
                    "http://localhost:8000/chat",
                    json={"message": prompt},
                    timeout=60
                )
                response.raise_for_status()
                data = response.json()
                
                # Show routing info
                st.info(f"🧭 {data['routing_display']}")
                
                # Show tools called
                if data['tools_called']:
                    st.code(f"🔧 Tools called: {', '.join(data['tools_called'])}", language=None)
                
                # Show response
                st.markdown(data['response'])
                
                # Show metadata
                st.caption(f"⏱️ {data['latency_ms']:.0f}ms | trace: {data['trace_id']}")
                
                # Save to history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": data['response'],
                    "routing_display": data['routing_display'],
                    "tools_called": data['tools_called'],
                    "latency_ms": data['latency_ms'],
                    "trace_id": data['trace_id']
                })
            except Exception as e:
                st.error(f"Error: {e}")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"Error: {e}"
                })

# Sidebar with info
with st.sidebar:
    st.header("🏗️ Architecture")
    st.markdown("""
    **Active Agents:**
    - 🟢 Order Agent (:9101)
    - 🟢 Inventory Agent (:9102)
    - 🟢 Cart Agent (:9103)
    
    **MCP Server:**
    - 🟢 Java Spring Boot (:8080)
    
    **LLM:**
    - 🟢 Qwen2.5:7b-8k (Ollama)
    """)
    
    if st.button("🔄 Clear Chat"):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    st.markdown("**Try these:**")
    st.markdown("- What's the status of order 1?")
    st.markdown("- How many mice in stock?")
    st.markdown("- Add 2 keyboards to cart")
    st.markdown("- Checkout please")