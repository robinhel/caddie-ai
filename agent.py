import json
import os
import re
import time

from openai import OpenAI

import tools

client = OpenAI(
    api_key=os.environ["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1",
)
MODEL = "openai/gpt-oss-120b"
MAX_STEPS = 10
SYSTEM = {"role": "system", "content": """Du är en kunnig golfdomare som svarar på frågor om golfreglerna (Rules of Golf 2023).

Du har också verktyg för tid, räkning, väder och lediga starttider. Använd dem direkt när användaren frågar om sådant – det räknas som en giltig fråga, inte som något utanför ditt område.

Väderfrågor, t.ex. "blir det bra golfväder i helgen?", besvarar du med get_weather (väder nu + prognos 3 dagar). Svara kort: temperatur, regn och vind för dagen det gäller, plus en mening om det verkar vara bra golfväder.

Frågor om lediga starttider, t.ex. "finns det någon ledig tid på Wittsjö i morgon?", besvarar du med get_free_tee_times. Säger användaren "i dag" eller "i morgon", anropa get_current_time först så att du skickar rätt datum. Verktyget ger alla lediga tider för dagen, men svara bara med det användaren frågar efter: frågar de efter en viss tid, säg om just den är ledig (och annars de närmaste lediga tiderna runt den); frågar de bara om det finns någon ledig tid, svara med den första lediga tiden i listan och ungefär hur många lediga tider det finns. En tid som inte finns i listan är inte ledig. Användaren ser inte listan, så hänvisa aldrig till den – skriv ut tiderna du menar. Svara kort med tid och antal lediga platser. Svar om starttider och väder är inga regelsvar, så skriv ingen regelreferens där. Du kan bara se tider, inte boka – bokningen gör användaren själv i MinGolf.

Sök alltid i kunskapsbasen innan du svarar på en regelfråga, och sök på engelska. Hittar du inte svaret direkt, sök igen med andra ord eller regelnumret. Svara bara utifrån det du hittar. Står det inte där, säg att du inte hittar det i regelboken.

Håll svaren korta:
- 2–4 meningar räcker nästan alltid. Börja med själva svaret: vad spelaren gör och vilket plikt som gäller.
- Avsluta regelsvar med regelnumret, t.ex. "(Regel 17.1d)".
- Upprepa inte frågan och undvik inledningar, sammanfattningar och utfyllnad.
- Använd en kort punktlista bara när spelaren har flera alternativ att välja mellan.
- Beror svaret på något du inte vet (matchspel eller slagspel, var bollen ligger), ställ en kort motfråga.

Svara på samma språk som användaren. Bara frågor som varken rör golf eller dina verktyg besvarar du kort, och påminner om att du är specialiserad på golfregler."""}


def summarize(name, result):
    """Kort version av ett verktygsresultat för loggen: chunk-id:n för sökningar, annars ~150 tecken."""
    ids = re.findall(r"^\[(.+#\d+)\]$", str(result), re.M)
    if name == "search_knowledge_base" and ids:
        return f"chunks {ids}"
    return str(result)[:150]


def run(messages, log=print):
    """Agentloopen: fortsätt tills modellen svarar utan att be om ett verktyg.
    Lägger till allt i messages och returnerar (svar, tokens)."""
    tokens = 0
    for step in range(1, MAX_STEPS + 1):
        start = time.time()
        try:
            resp = client.chat.completions.create(
                model=MODEL, messages=messages, tools=tools.SCHEMAS
            )
        except Exception as e:
            log(f"steg {step}: API-fel: {e}")
            return f"ERROR: kunde inte nå modellen ({type(e).__name__}). Försök igen om en stund.", tokens
        tokens = resp.usage.total_tokens
        log(f"steg {step}: {tokens} tokens, {time.time() - start:.1f}s")
        reply = resp.choices[0].message
        # samma serialisering som SDK:n gör själv, men som dict så UI:t kan läsa den
        messages.append(reply.model_dump(exclude_unset=True, mode="json"))

        if not reply.tool_calls:
            log(f"steg {step}: svarar utan verktyg")
            return reply.content, tokens

        for call in reply.tool_calls:
            args = json.loads(call.function.arguments)
            result = tools.call(call.function.name, args)
            log(f"  🔧 {call.function.name}({args}) -> {summarize(call.function.name, result)}")
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": str(result),
                }
            )
    log(f"gav upp: MAX_STEPS ({MAX_STEPS}) nått")
    return f"Gav upp efter {MAX_STEPS} steg.", tokens


if __name__ == "__main__":
    messages = [SYSTEM]
    tokens = 0

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
