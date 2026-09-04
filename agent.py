import os

from openai import OpenAI

client = OpenAI(
    api_key=os.environ["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1",
)

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
        model="openai/gpt-oss-120b",
        messages=messages,
    )
    reply = resp.choices[0].message.content
    messages.append({"role": "assistant", "content": reply})
    tokens = resp.usage.prompt_tokens + resp.usage.completion_tokens
    print(reply)
