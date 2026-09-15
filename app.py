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

calls = {}  # tool_call_id -> "namn(argument)", så resultatet hamnar under rätt anrop
for m in st.session_state.messages:
    if m["role"] in ("user", "assistant") and m.get("content"):
        st.chat_message(m["role"]).write(m["content"])
    for c in m.get("tool_calls") or []:
        calls[c["id"]] = f"{c['function']['name']}({c['function']['arguments']})"
    if m["role"] == "tool":
        with st.expander(f"🔧 `{calls[m['tool_call_id']]}`"):
            st.text(m["content"])

if prompt := st.chat_input("Fråga något...", submit_mode="disable"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.spinner("Tänker..."):
        answer, st.session_state.tokens = agent.run(st.session_state.messages)
    if answer and answer.startswith("ERROR"):
        st.chat_message("user").write(prompt)
        st.error(answer)
    else:
        st.rerun()
