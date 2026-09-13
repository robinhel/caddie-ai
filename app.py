import streamlit as st

import agent

st.title("LIA-agent")

if "messages" not in st.session_state:
    st.session_state.messages = [agent.SYSTEM]
    st.session_state.tokens = 0

with st.sidebar:
    st.metric("Tokens i historiken", st.session_state.tokens)
    if st.button("Ny chatt"):
        del st.session_state.messages  # blocket ovan återställer allt vid rerun
        st.rerun()

for m in st.session_state.messages:
    # assistant utan content är ett verktygsanrop, inget att visa
    if m["role"] in ("user", "assistant") and m.get("content"):
        st.chat_message(m["role"]).write(m["content"])
    elif m["role"] == "tool":
        st.caption(f"🔧 {m['content'][:200]}")

if prompt := st.chat_input("Fråga något...", submit_mode="disable"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.spinner("Tänker..."):
        _, st.session_state.tokens = agent.run(
            st.session_state.messages, log=lambda _: None
        )
    st.rerun()
