# Praktikuppgift: Bygg en AI-agent från grunden

**Digital Step** • Självstudie i agentutveckling, RAG och LLM-integration

Välkommen! Det här är en självstudieuppgift som ska ge dig praktisk förståelse för hur moderna AI-agenter byggs. Du kommer att gå från noll till en fungerande agent som kan svara på frågor mot en egen kunskapsdatabas, anropa verktyg och föra en dialog över flera steg.

Tanken är inte att du ska följa en mall, utan att du själv ska bygga, läsa, fråga och förstå. Det viktigaste är inte att du blir klar med allt — det viktigaste är att du förstår vad som händer under huven på de produkter som vi alla använder dagligen (ChatGPT, Claude, Cursor osv).

---

## Vad du behöver veta först

- Du jobbar mot **Berget AI** — en svensk AI-leverantör där all data stannar inom EU. Vi har konto med pengar på och förser dig med API-nyckel. Säg till så fixar vi det.
- Berget exponerar ett **OpenAI-kompatibelt API** på `https://api.berget.ai/v1`, vilket betyder att du kan använda den vanliga `openai`-Python-SDK:n och bara peka om `base_url` till Bergets endpoint. Det är så vi själva integrerar mot dem på Digital Step via vår egna AI-harness.
- Allt arbete sker i **Python** till att börja med. Använd virtuella miljöer (venv, uv, eller poetry — välj det du föredrar). Versionshantera med git från dag ett är ett råd så du kan spara det som ett projekt i slutändan att visa upp.

---

## Lärandemål

Efter den här uppgiften ska du själv kunna förklara följande begrepp för en kollega — inte bara känna igen dem, utan kunna rita upp dem på en whiteboard:

### Kärnområden

- **Prompt engineering** — hur man skriver instruktioner till en LLM så att man får tillförlitliga, strukturerade svar.
- **Structured outputs** — LLM:en outputtar inte i en vanlig string utan i en JSON som vi kan läsa av nycklar på och sedan parsa ut värdena dit vi vill.
- **Context engineering** — hur man bygger upp och hanterar det "sammanhang" som modellen ser i varje anrop. Skillnaden mellan system prompt, user prompt, conversation history, retrieved context och tool results.
- **Tools (function calling)** — hur man definierar verktyg som modellen kan anropa, och hur man hanterar resultaten.
- **Agent loop** — själva kärnan i en agent. Hur loopen ser ut, när den avslutas, vad som händer i varje iteration.
- **RAG (Retrieval-Augmented Generation)** — varför, när och hur.
- **Vektordatabas** — vad embeddings är, hur similarity search fungerar, och vilka avvägningar som finns.

### Överkurs (kuriosa, men superintressant)

- **Subagents** — agenter som spawnar andra agenter för delproblem.
- **Agent harness** — det "skal" som omger agenten: tool registry, autentisering, loggning, säkerhet, retry-logik. Det här är vad vi själva byggt på Digital Step.

### Bonus om du har tid

- Byt ut RAG mot file search-verktyg (`list_documents`, `search_documents`, `read_document`) och se vad som händer med kvaliteten på svaren när en AI söker i rå text istället för att räkna på vektorer.
- Gör om lösningen till Go. Det är så vi kör i produktion — och det är en bra övning i att skilja på vad som är konceptuellt vs. vad som är språkspecifikt.
- Bygg en frontend. Det räcker med backend-delen egentligen, men du kan alltid be Claude eller något bygga en enkel frontend åt dig.

---

## Förkunskaper och setup

### Vad du bör kunna innan du börjar

- Grundläggande Python (funktioner, klasser, list/dict comprehensions, async/await på grundnivå).
- Hur man läser API-dokumentation och gör HTTP-anrop.
- Git: clone, commit, push, branch.

### Vad du inte behöver kunna

- Maskininlärning eller matematiken bakom transformers. Det är fine att se LLM:en som en black box som tar in text och returnerar text.
- Avancerad systemarkitektur. Vi jobbar oss dit i steg.

### Verktyg du behöver

| Verktyg | Vad och varför |
| --- | --- |
| **Python 3.11+** | Allt i del 1–6 är i Python. |
| **Git** | Versionshantera från dag ett. Pusha till GitHub eller GitLab. |
| **VS Code / Cursor** | Vilken editor som helst funkar, men Cursor/Claude Code/Codex kan vara intressant att prova just för det här projektet — då upplever du själv hur en agent som bygger kod känns. Vi använder främst Claude Code hos oss. |
| **Berget AI-nyckel** | Vi förser dig. Lägg den i `.env` som `BERGET_API_KEY` och committa **ALDRIG** den filen till GitHub. |
| **openai SDK** | Berget är OpenAI-kompatibelt, så `pip install openai` och peka `base_url` till `https://api.berget.ai/v1` så är det löst snabbt. |
| **uv eller venv** | Virtuella miljöer. `uv` är snabbare och mer modernt, `venv` är inbyggt. |
| **ChromaDB** | En enkel vektordatabas att börja med. Lokalt, ingen server. |

> **Säkerhetsregel #1**
> Pusha aldrig API-nycklar till git. Använd `.env` och `.gitignore`. Superviktigt, då en läckt API-nyckel kan kosta skjortan om någon snor den och använder den. Är du osäker kan jag hjälpa dig.

---

## Uppgiften — bygg i steg

Du jobbar i sju steg. Varje steg bygger vidare på det förra. Tanken är att du efter varje steg ska ha något som faktiskt funkar och som du kan visa upp. Resistera frestelsen att hoppa fram — det är repetitionen i loopen som är poängen.

### Steg 1 — Hello LLM

**Mål:** Få ett första API-anrop att fungera. Du ska kunna skicka en sträng till en LLM och få tillbaka ett svar.

**Vad du gör**

- Sätt upp projektmapp med venv/uv och git.
- `pip install openai python-dotenv`
- Lägg din `BERGET_API_KEY` i en `.env`-fil. Lägg `.env` i `.gitignore`.
- Skriv ett enkelt script som tar en fråga från CLI och printar svaret. Du kan använda det vanliga OpenAI-biblioteket eller t.ex. LangGraph för mer plug-and-play.

**Reflektera och skriv ner svaren**

- Vad är en "system prompt" och hur skiljer den sig från en "user prompt"?
- Vad händer om du sätter `temperature` till 0 vs. 1? Testa samma fråga 3 gånger på respektive nivå.
- Vad är `max_tokens` egentligen — och varför skulle det någonsin vara en begränsning? Testa med olika värden här och se resultatet.

### Steg 2 — Prompt engineering & structured output

**Mål:** Förstå hur formuleringen påverkar resultatet. Du ska kunna styra modellen att producera exakt det format du vill ha.

**Vad du gör**

- Skriv en prompt som ber modellen klassificera en fritext-input som något av: `"fråga"`, `"klagomål"`, `"beröm"`, `"annat"`. Den ska svara med ENDAST en JSON: `{"category": "...", "confidence": 0.0-1.0}`.
- Testa med 10 olika inputs. Hur ofta får du exakt det format du bad om?
- Förbättra prompten tills modellen är pålitlig. Prova: tydligare instruktioner, exempel (few-shot), tvinga JSON via API-parametrar om SDK:n stödjer det.
- Lägg in i modellens objekt att använda structured outputs.

**Reflektera**

- Vad var det som faktiskt gjorde störst skillnad — exempel, formatering, eller specifika ord?
- Vad händer om du ber modellen "think step by step" innan den svarar? Hur påverkar det kvaliteten? Hastigheten?
- Vad är skillnaden mellan zero-shot, one-shot och few-shot prompting?

### Steg 3 — Context engineering: bygg en chatt

**Mål:** Få modellen att minnas vad ni pratade om för 5 svar sedan. Här lär du dig att hantera conversation history.

**Vad du gör**

- Bygg en CLI-chatt där användaren kan skriva flera meddelanden i rad.
- Skicka ALLA tidigare meddelanden (både användarens och modellens) i varje API-anrop.
- Lägg till ett `/reset`-kommando som rensar historiken.
- Lägg till ett `/tokens`-kommando som visar uppskattat antal tokens i den nuvarande conversation history.

**Reflektera**

- Hur många tokens drar din historik efter 10 utbyten? 50?
- Vad händer när du närmar dig modellens context window-gräns?
- Vad är skillnaden mellan att klippa bort gamla meddelanden vs. att summera dem?

> **Context engineering vs. prompt engineering**
> Det här är en distinktion som blivit viktigare det senaste året. Prompt engineering = hur du formulerar instruktioner. Context engineering = vad du faktiskt stoppar in i context windowet och i vilken ordning. För agenter spelar det andra mycket större roll. Du kommer att märka det själv när du kommer till RAG.

### Steg 4 — Tools (function calling)

**Mål:** Låt modellen anropa Python-funktioner. Det är här agenter börjar bli intressanta.

**Vad du gör**

- Definiera tre simpla verktyg: `get_current_time()`, `calculate(expression)`, `get_weather(city)`. Sista får mocka — typ alltid "15 grader och soligt".
- Använd din SDK:s tool/function calling-API för att exponera dem för modellen.
- Skriv koden som tar emot `tool_use` från modellen, anropar funktionen, och skickar tillbaka `tool_result`.
- Testa: "Vad är klockan, och vad är 47 \* 213?"

**Reflektera**

- Vad händer om modellen ber om ett verktyg med fel argument? Hur ska du hantera det?
- Vad händer om verktyget kastar ett undantag? Ska modellen få veta det?
- Hur beskriver du verktyget för modellen så att den vet när den ska använda det?

### Steg 5 — Agent loop

**Mål:** Bygg loopen. När du är klar här så har du byggt en agent.

**Vad du gör**

- Implementera den här loopen ovanpå koden från Steg 4.
- Lägg till skydd mot infinite loops (max 10 iterationer t.ex.).
- Logga varje iteration: vilket verktyg som kallades, med vilka argument, vad som returnerades.
- Testa med en fråga som kräver flera verktygsanrop i sekvens: "Vad är klockan i Stockholm? Räkna sedan ut hur många minuter det är till midnatt."

**Reflektera**

- Vad är det egentligen som gör en agent till en agent? (Ledtråd: det är den här loopen.)
- Vad är riskerna med att låta loopen köra utan `max_iterations`?
- Hur skulle du veta om agenten har fastnat i ett ologiskt mönster? (Typ kallar samma verktyg om och om.)

> **Det här är vad alla agenter är**
> Cursor, Claude Code, ChatGPT med tools — allihopa är varianter av den här loopen. Det blir komplicerat senare, men kärnan är exakt det här. När du fattar det här har du fattat 70 % av allt.

### Steg 6 — RAG och vektordatabas

**Mål:** Ge agenten tillgång till kunskap som inte finns i modellens träningsdata. Du väljer själv vad den ska kunna. Här kan det vara bra att förstå koncept som chunking, embedding och retrieval innan du börjar implementera det själv.

**Välj din kunskapsdatabas**

Välj något du själv är intresserad av — det blir mer kul. Förslag:

- Dokumentationen för ett bibliotek eller verktyg du gillar
- Wikipedia-artiklar inom ett ämne
- Receptsamlingar, regler för ett brädspel, lagtexter, manualer
- Egna anteckningar, böcker du läst, podcastutskrifter

**Vad du gör**

- Samla in 20–100 dokument inom ditt valda område (PDF:er, markdown-filer, webbsidor — vad du vill).
- Chunka dem — dela upp i bitar på cirka 500–1000 tokens. Tänk på att du vill behålla mening, inte klippa mitt i en mening.
- Generera embeddings för varje chunk via Berget AI:s embeddings-endpoint (samma OpenAI-kompatibla API, bara `client.embeddings.create` istället för `chat.completions`). Berget har dedikerade embedding-modeller — kolla console.berget.ai/models.
- Spara i ChromaDB lokalt.
- Bygg en `search_knowledge_base(query)`-funktion som tar en fråga, embeddar den, och returnerar de 3–5 mest relevanta chunks.
- Lägg till `search_knowledge_base` som ett verktyg i din agent från Steg 5.
- Testa! Fråga agenten saker som kräver kunskap från din databas.

**Reflektera**

- Vad är en embedding egentligen?
- Vad händer om du chunkar för smått? För stort?
- Hur skulle du mäta om din RAG faktiskt fungerar bra?
- När misslyckas RAG? Kan du producera en fråga som ser rimlig ut men där agenten ger fel svar?

> **Insikt**
> RAG är inte magi. Det är: "hitta relevant text och stoppa in den i prompten innan modellen svarar." Det är hela tricket. Komplexiteten ligger i att hitta bra text — det är där 90 % av jobbet är.

### Steg 7 — Putsa och dokumentera

**Mål:** Något du faktiskt vågar visa upp.

- Skriv en README som förklarar: vad agenten gör, hur man kör den, vilken kunskapsdatabas den har, exempel på frågor.
- Lägg in tydlig loggning så att man kan se vad agenten gör i varje steg.
- Hantera felfall: vad händer om API:et är nere? Om vektordatabasen är tom? Om en tool kraschar?
- Skriv minst 3 enhetstester (verktygen är lättast att testa).

---

## Överkurs

De här delarna är kuriosa-nivå. Du behöver inte göra dem, men om du har tid och nyfikenhet så är det här superrelevant för det vi själva jobbar med.

### Subagents

Tanken: huvudagenten kan, som ett verktyg, spawna en "hjälpagent" som får ett delproblem och en egen tool-uppsättning. Hjälpagenten kör sin egen loop och returnerar bara slutresultatet.

**Varför är det här intressant?**

- Det håller huvudagentens context rent — den ser bara delresultatet, inte alla mellansteg.
- Det låter dig parallellisera (kör flera subagents samtidigt).
- Det låter dig ge olika subagents olika behörigheter.

**Vad du kan testa**

Implementera ett `spawn_research_agent(question)`-verktyg som internt kör en mini-agent som får använda `search_knowledge_base` ett antal gånger och sedan returnerar en sammanfattning. Huvudagenten ser bara den sammanfattningen.

### Agent harness

Det här är vad vi själva bygger på Digital Step. Ett "harness" är allt det runt själva agent-loopen som behövs för att den ska vara säker och hanterbar i produktion:

- **Tool registry** — en central plats där verktyg registreras med scheman, behörigheter, beskrivningar.
- **Authentication & authorization** — vem får använda vilket verktyg? För oss handlar det om RBAC och tenant scoping i en JWT.
- **Audit logging** — append-only logg av varje tool-anrop. Vem, när, med vilka argument, vad blev resultatet.
- **Rate limiting och timeout** — hur skyddar man sig mot en agent som går bananas?
- **Prompt template management** — system prompts versionshanterade och injicerade vid runtime.

Du behöver inte bygga det här — bara läsa på och förstå varför det behövs. Det är skillnaden mellan ett hobbyprojekt och något som får hantera känslig data.

### File search istället för RAG

Det här är ett nytt och spännande mönster. Istället för embeddings + vektordatabas, ge agenten verktyg som efterliknar hur en människa skulle leta:

- `list_documents(directory)` — vad finns det för dokument?
- `search_documents(query)` — grep / full-text search.
- `read_document(path, line_range)` — läs en specifik del.

Modellen får alltså själv navigera istället för att du gör en upfront retrieval. Det är hur Claude Code och liknande verktyg jobbar mot kodbas.

**Jämför**

- När fungerar RAG bättre? (Kort fråga, stort dokumentbestånd, tydligt formulerade frågor.)
- När fungerar file search bättre? (Strukturerad data, behov av att utforska, multi-step research-frågor.)

### Refaktorera till Go

Vi kör Go i produktion på Digital Step. Att portera den här lösningen från Python till Go är en jättebra övning för dig.

**Vad du kommer märka**

- Tool definitions blir mycket mer explicita. Du kan inte fuska med typer.
- Concurrency blir enkelt med goroutines — och plötsligt blir parallella subagents väldigt naturliga.
- Strukturen tvingar dig att tänka tydligare på interfaces. Vad är en agent? Vad är ett tool? Vad är en harness?

Använd standard `net/http` eller en lättviktsklient mot LLM-API:et. För vektordatabas kan du köra ChromaDB över HTTP, eller byta till `qdrant-go-client`.

### Frontend (frivilligt men kul)

Du behöver inte bygga något UI. Men om du vill, är det här bra alternativ:

- **Streamlit** — Python-baserat, du får en chattruta på 20 rader kod.
- **Gradio** — liknande, fokus på AI-demos.
- **Be din agent implementera en frontend åt dig**, easy peasy. Gärna i Next.js i så fall, så du kan förstå Server Side Rendering och vad ett "BFF-pattern" är.

> **Tips**
> Om du bygger frontend, lägg energin på att visualisera vad agenten faktiskt gör. När den anropar ett verktyg, visa det. När den hämtar context från RAG, visa vilka chunks. Det här är 80 % av varför Claude Code och Cursor känns magiska — de visar dig sin tankegång.

---

## Avstämning och redovisning

**Hur vi jobbar tillsammans under uppgiften**

- Du kan höra av dig när som helst med frågor på mail: marcus.turesson@digitalstep.se
- Pusha till git ofta. Hellre många små commits än få stora.

**Slutredovisning**

När du är klar (eller när tiden är slut) kör vi en gemensam genomgång där:

- Du visar agenten i drift. Live-demo med några exempel-frågor.
- Du går igenom kodstrukturen och förklarar de centrala designvalen.
- Du svarar på frågor från oss. ("Vad händer om jag ställer den här frågan? Varför är det så?")
- Du presenterar vad du tycker är intressant att utforska vidare.

---

## Resurser

**Officiell dokumentation**

- **Berget AI** — berget.ai/developers samt console.berget.ai/models. Här hittar du modellutbud, prissättning och endpoints. Fråga mig annars om vilka modeller du borde testa osv. Gemma4 är en bra modell på typ allt.
- **OpenAI Python SDK** — github.com/openai/openai-python. Eftersom Berget är OpenAI-kompatibelt så är det den här SDK:n du faktiskt använder.
- **OpenAI API-referens (function calling, tool use)** — platform.openai.com/docs. Det är det API-format Berget följer.
- **ChromaDB docs** — docs.trychroma.com. Liten och pedagogisk.

**Att läsa**

- Anthropic: "Building effective agents" — grym artikel om vilka mönster som fungerar och vilka som inte gör det. Läs den här FÖRE du börjar Steg 5.
- Anthropic: "Effective Context Engineering" — galet bra innehåll om context engineering.

**Att titta på**

- Andrej Karpathy: "Intro to Large Language Models" på YouTube. En timme, värd varje minut.
- Andrej Karpathy: "Deep Dive into LLMs like ChatGPT"
- RAG Crash Course for Beginners
- What is OpenClaw? Inside AI Agents, LLMs and the Agentic Loop

**Tumregler från oss**

- Det är fine att fråga ChatGPT/Claude om hjälp med koden. Men FÖRSTÅ varje rad innan du committar den.
- När du gör något du inte förstår — lyft det till mig eller din AI.
- Skriv ner dina egna lärdomar i en `NOTES.md` i repot. Den är guld värd när du ska redovisa.
