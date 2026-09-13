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
SYSTEM = {"role": "system", "content": "Du är en hjälpsam assistent."}


def run(messages, log=print):
    """Agentloopen: fortsätt tills modellen svarar utan att be om ett verktyg.
    Lägger till allt i messages och returnerar (svar, tokens)."""
    for step in range(MAX_STEPS):
        resp = client.chat.completions.create(
            model=MODEL, messages=messages, tools=tools.SCHEMAS
        )
        reply = resp.choices[0].message
        # samma serialisering som SDK:n gör själv, men som dict så UI:t kan läsa den
        messages.append(reply.model_dump(exclude_unset=True, mode="json"))

        if not reply.tool_calls:
            return reply.content, resp.usage.total_tokens

        for call in reply.tool_calls:
            args = json.loads(call.function.arguments)
            result = tools.call(call.function.name, args)
            log(f"  step {step + 1}: {call.function.name}({args}) -> {result}")
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": str(result),
                }
            )
    return f"Gav upp efter {MAX_STEPS} steg.", resp.usage.total_tokens


if __name__ == "__main__":
    messages = [SYSTEM]
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
        answer, tokens = run(messages)
        print(answer)
