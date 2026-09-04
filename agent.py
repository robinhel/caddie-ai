import json
import os

from openai import OpenAI

import tools

client = OpenAI(
    api_key=os.environ["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1",
)
MODEL = "openai/gpt-oss-120b"

messages = [{"role": "system", "content": "Du är en hjälpsam assistent."}]
tokens = 0

print("Hej! Vad kan jag hjälpa dig med idag?")

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
    resp = client.chat.completions.create(
        model=MODEL, messages=messages, tools=tools.SCHEMAS
    )
    reply = resp.choices[0].message
    messages.append(reply)

    if reply.tool_calls:
        for call in reply.tool_calls:
            args = json.loads(call.function.arguments)
            result = tools.call(call.function.name, args)
            print(f"  [{call.function.name}({args}) -> {result}]")
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": str(result),
                }
            )
        resp = client.chat.completions.create(
            model=MODEL, messages=messages, tools=tools.SCHEMAS
        )
        messages.append(resp.choices[0].message)

    tokens = resp.usage.prompt_tokens + resp.usage.completion_tokens
    print(resp.choices[0].message.content)
