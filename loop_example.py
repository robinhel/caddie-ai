"""Same agent as agent.py, but with the tool handling wrapped in an agent loop.

Compare the middle of the while-loop with agent.py:40-55.
"""

import json
import os

from openai import OpenAI

import tools

client = OpenAI(
    api_key=os.environ["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1",
)
MODEL = "openai/gpt-oss-120b"
MAX_STEPS = 10

messages = [{"role": "system", "content": "Du är en hjälpsam assistent."}]
tokens = 0

print("Hej! Vad kan jag hjälpa dig med idag?")

# kommando
while True:
    user_input = input("> ")
    if user_input in ("quit", "exit"):
        break
    if not user_input:
        continue
    if user_input == "/reset":
        del messages[1:]
        tokens = 0
        continue
    if user_input == "/tokens":
        print(f"{tokens} tokens i historiken")
        continue

    messages.append({"role": "user", "content": user_input})

    # The agent loop: keep going until the model answers without asking for a tool.
    for step in range(MAX_STEPS):
        resp = client.chat.completions.create(
            model=MODEL, messages=messages, tools=tools.SCHEMAS
        )
        reply = resp.choices[0].message
        messages.append(reply)

        if not reply.tool_calls:
            break

        for call in reply.tool_calls:
            args = json.loads(call.function.arguments)
            result = tools.call(call.function.name, args)
            print(f"  step {step + 1}: {call.function.name}({args}) -> {result}")
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": str(result),
                }
            )
    else:
        print(f"Gav upp efter {MAX_STEPS} steg.")

    tokens = resp.usage.prompt_tokens + resp.usage.completion_tokens
    print(reply.content)
