# LIA-agent – en golfregel-assistent

Det här är en liten AI-agent som jag byggt under min LIA. Man ställer frågor om golfreglerna och agenten letar upp svaret i den officiella regelboken, i stället för att hitta på något. Tanken var att lära mig hur en agent faktiskt fungerar under huven: loopen, verktygen och RAG. Därför är allt skrivet för hand, utan ramverk som LangChain.

## Vad agenten gör

När du ställer en fråga skickas den till en språkmodell (`gpt-oss-120b` via Groq). Modellen får själv avgöra om den behöver använda något verktyg innan den svarar:

- **`search_knowledge_base`** söker i golfreglerna och hämtar de tre mest relevanta textbitarna. Det är den viktigaste funktionen.
- **`calculate`** räknar ut matte, t.ex. hur många slag det blir med plikt. Den kör bara siffror och `+ - * / % **`, aldrig godtycklig kod.
- **`get_current_time`** ger dagens datum och tid.
- **`get_weather`** hämtar vädret just nu och en prognos på 3 dagar från Open-Meteo (gratis, ingen API-nyckel).

Agenten kör i en loop: modellen ber om ett verktyg, får resultatet och kan be om ett till. Det fortsätter tills den har ett svar, men högst 10 steg så att den inte fastnar.

## Kunskapsdatabasen

Kunskapen kommer från **The Rules of Golf, 2023 edition** från R&A och USGA (`docs/rules_of_golf_2023.md`). Texten är på engelska.

Så här funkar det:

1. `rag.py` delar upp regelboken i bitar på ungefär 800 tecken. Bitarna överlappar lite, så att en mening inte klipps av mitt i ett sammanhang.
2. Bitarna sparas i en lokal vektordatabas, [Chroma](https://www.trychroma.com/), i mappen `chroma/`.
3. När agenten söker plockar Chroma fram de tre bitar som betyder mest likt frågan.

Eftersom embeddingmodellen är bäst på engelska ber jag agenten att alltid söka på engelska, även när du skriver på svenska. Det gjorde stor skillnad för träffarna.

## Kom igång

Du behöver [uv](https://docs.astral.sh/uv/) och en gratis API-nyckel från [Groq](https://console.groq.com/).

1. Skapa en fil som heter `.env` i projektmappen:

   ```
   GROQ_API_KEY=din-nyckel-här
   ```

2. Indexera regelboken (första gången laddas embeddingmodellen ner, så det tar en stund):

   ```
   uv run rag.py
   ```

   Kör om det här varje gång du ändrar något i `docs/`, annars ser agenten inte det nya.

3. Starta agenten, antingen i webbläsaren:

   ```
   uv run --env-file .env streamlit run app.py
   ```

   eller i terminalen:

   ```
   uv run --env-file .env agent.py
   ```

   I terminalen kan du skriva `/reset` för att börja om, `/tokens` för att se hur stor historiken är och `exit` för att avsluta.

I webbappen syns verktygsanropen som små 🔧-rader, så man kan se vad agenten letade fram innan den svarade.

## Exempel på frågor

- Min boll hamnade i vattnet, vad får jag göra?
- Får jag flytta en lös pinne som ligger bredvid bollen i bunkern?
- Vad är skillnaden mellan en provisorisk boll och en vanlig?
- Hur lång tid har jag på mig att leta efter min boll?
- Vad räknas som "ground under repair"?
- Jag slog ut ur banan två gånger på samma hål, hur många slag har jag då?

## Testa

`tools.py` har några enkla tester längst ner i filen:

```
uv run tools.py
```

## Begränsningar

- Agenten vet bara det som står i regelboken. Lokala regler eller tolkningar från din klubb känner den inte till.
- Den hämtar bara tre textbitar per sökning. Ibland missar den därför något, och då måste den söka igen.
