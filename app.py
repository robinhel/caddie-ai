import streamlit as st

import agent

st.title("LIA-agent")

if "messages" not in st.session_state:
    st.session_state.messages = [agent.SYSTEM]

for m in st.session_state.messages:
    # assistant utan content är ett verktygsanrop, inget att visa
    if m["role"] in ("user", "assistant") and m.get("content"):
        st.chat_message(m["role"]).write(m["content"])
    elif m["role"] == "tool":
        st.caption(f"🔧 {m['content'][:200]}")

if prompt := st.chat_input("Fråga något...", submit_mode="disable"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.spinner("Tänker..."):
        agent.run(st.session_state.messages, log=lambda _: None)
    st.rerun()
