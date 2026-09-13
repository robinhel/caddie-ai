# Streamlit i småsteg

Prompts att köra en i taget mot din kodagent. Kör klart-checken efter varje steg
innan du går vidare — poängen är att aldrig ha mer än ett trasigt steg åt gången.

Förkunskap: agenten (`agent.py` + `tools.py`) fungerar i terminalen, gärna med
RAG-verktyget från `rag.md`.

---

## Steg 0 — Beroende

```
Lägg till streamlit som dependency i pyproject.toml och installera.
```

**Klart när:** `uv run streamlit --version` skriver ut ett versionsnummer.

---

## Steg 1 — Gör agentloopen återanvändbar

```
agent.py kör sin chattloop direkt vid import, så den går inte att använda från
en annan fil. Flytta agentloopen till en funktion run(messages, log=print) som
lägger till alla meddelanden i messages och returnerar (svar, tokens). Spara
modellens svar som dict med reply.model_dump(exclude_unset=True, mode="json")
istället för som objekt, så att ett UI kan läsa historiken. Bryt ut
systemprompten till en konstant SYSTEM. Lägg input-loopen, /reset och /tokens
under if __name__ == "__main__": och låt den anropa run().
```

**Klart när:** `uv run --env-file .env agent.py` fungerar precis som förut —
fråga vad klockan är, loggraden `get_current_time({})` syns, och `/tokens` svarar.

**Fundera:** varför en `log`-parameter istället för `print` direkt i loopen?

---

## Steg 2 — Minsta möjliga chatt

```
Skapa app.py: en st.title, och historiken i st.session_state.messages som
startar som [agent.SYSTEM]. Rita upp alla user- och assistant-meddelanden med
st.chat_message (hoppa över assistant-meddelanden utan content, det är
verktygsanrop). Med st.chat_input: lägg till frågan i historiken, kör
agent.run(st.session_state.messages, log=lambda _: None) inuti en st.spinner,
och avsluta med st.rerun() så att det nya svaret ritas upp.
```

**Klart när:** `uv run --env-file .env streamlit run app.py`, ställ två frågor
efter varandra — båda frågorna och svaren ligger kvar i fönstret.

**Fundera:** Streamlit kör om hela skriptet vid varje klick. Vad händer med
historiken om du lägger `messages = [agent.SYSTEM]` direkt i skriptet istället
för i `session_state`?

---

## Steg 3 — Visa verktygsanropen

```
Visa meddelanden med role "tool" i app.py som en st.caption med 🔧 framför och
innehållet kapat till 200 tecken, så man ser vad agenten gjorde utan att
sökträffarna tar över skärmen.
```

**Klart när:** fråga "Vad är 47 * 213?" — raden `🔧 10011` syns ovanför svaret.

---

## Steg 4 — Sidopanel

```
Lägg en st.sidebar i app.py med en st.metric som visar antal tokens i
historiken (spara det run() returnerar i st.session_state.tokens) och en knapp
"Ny chatt" som tömmer historiken och kör st.rerun().
```

**Klart när:** tokens växer för varje fråga, och "Ny chatt" ger ett tomt fönster.

---

## Steg 5 — Testa utan webbläsare och dokumentera

```
Lägg till i README hur man startar appen:
uv run --env-file .env streamlit run app.py
Skriv sedan ett litet skript som kör app.py med streamlit.testing.v1.AppTest,
skickar "Vad är 47 * 213?" via chat_input och skriver ut chattmeddelandena,
captions och at.exception.
```

**Klart när:** skriptet skriver ut svaret med 10011, en `🔧`-caption och en tom
exception-lista.

---

## Steg 6 — Felfall (det här är övningen)

**Fundera:** sätt `MAX_STEPS = 1` i `agent.py` och fråga något som kräver ett
verktyg. Terminalen skriver "Gav upp efter 1 steg." — vad visar appen? Laga det
så att användaren ser att agenten gav upp. Och vad händer i appen om
`GROQ_API_KEY` saknas?
