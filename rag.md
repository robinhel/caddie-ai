# RAG i småsteg

Prompts att köra en i taget mot din kodagent. Kör klart-checken efter varje steg
innan du går vidare — poängen är att aldrig ha mer än ett trasigt steg åt gången.

Förkunskap: agenten från Steg 5 (`agent.py` + `tools.py`) ska fungera.

---

## Steg 0 — Dokument att söka i

```
Skapa mappen docs/ och lägg in några .md- eller .txt-filer med text jag faktiskt
vill kunna fråga om. Kopiera in uppgift.md dit som ett första dokument.
```

**Klart när:** `ls docs/` visar minst en fil.

---

## Steg 1 — Beroenden

```
Lägg till chromadb som dependency i pyproject.toml och installera.
```

**Klart när:** `uv run python -c "import chromadb"` går igenom utan fel.

---

## Steg 2 — Chunkning (ren funktion, ingen databas)

```
Skapa rag.py med konstanterna DOCS = pathlib.Path("docs"), CHUNK = 800 tecken och
OVERLAP = 100, samt en funktion chunks(text) som delar text i bitar på ~CHUNK
tecken. Dela på tomrad (stycken) så att inget klipps mitt i en mening, och låt
OVERLAP tecken följa med in i nästa bit så att en mening på gränsen finns i båda.
Lägg ett __main__-block med assert som verifierar att lång text delas i flera
bitar, att bitarna håller sig nära CHUNK och att kort text blir exakt en bit.
```

**Klart när:** `uv run rag.py` går igenom utan AssertionError.

**Fundera:** varför tecken och inte tokens? Vad går sönder om CHUNK = 50?

---

## Steg 3 — Vektordatabasen

```
Lägg till en funktion collection() i rag.py som lat-initierar en
chromadb.PersistentClient("chroma") och returnerar collection "docs". Lat för att
Chroma laddar ner sin embedding-modell vid första anropet. Cacha i en modulglobal.
Lägg till chroma/ i .gitignore.
```

**Klart när:** `uv run python -c "import rag; print(rag.collection().count())"` skriver `0`.

---

## Steg 4 — Indexering

```
Lägg till ingest() i rag.py: läs alla .md- och .txt-filer under DOCS rekursivt,
chunka dem, och upserta dem i collection() med id "<filväg>#<index>". Använd
upsert så att omkörning skriver över istället för att dubblera. Returnera en
sträng med antal chunks, och en tydlig text om DOCS är tom. Anropa ingest() från
__main__ och skriv ut resultatet.
```

**Klart när:** `uv run rag.py` skriver "N chunks indexerade" och N > 0. Kör igen —
samma N, inte dubbelt.

---

## Steg 5 — Sökningen

```
Lägg till search_knowledge_base(query) i rag.py som hämtar de tre mest liknande
chunksen med col.query(query_texts=[query], n_results=3) och returnerar dem som
EN textklump, varje träff prefixad med sitt id och separerad med "---". Om
collection är tom, returnera "ERROR: kunskapsbasen är tom. Kör 'uv run rag.py' först."
```

**Klart när:** `uv run python -c "import rag; print(rag.search_knowledge_base('din fråga'))"`
ger relevant text tillbaka.

**Fundera:** träffarna innehåller inte nödvändigtvis frågans ord. Varför funkar det ändå?

---

## Steg 6 — Koppla in i agenten

```
Importera search_knowledge_base i tools.py, lägg den i FUNCTIONS och skriv ett
schema i SCHEMAS. Beskrivningen ska säga åt modellen att alltid söka innan den
svarar på frågor om innehåll som inte är allmänt känt, och att bara svara utifrån
det den får tillbaka. Parametern query beskrivs som "frågan, formulerad som den
skulle stå i dokumentet".
```

**Klart när:** `uv run --env-file .env agent.py` och en fråga vars svar bara finns
i docs/ — loggraden ska visa `search_knowledge_base(...)` innan svaret.

---

## Steg 7 — Felfall och dokumentation

```
Lägg till i README hur man indexerar (uv run rag.py) och att det måste köras om
när docs/ ändras. Verifiera att agenten ger ett begripligt svar när
kunskapsbasen är tom, inte en stacktrace.
```

**Klart när:** `rm -rf chroma && uv run --env-file .env agent.py` → agenten
berättar att basen är tom istället för att krascha.

---

## Steg 8 — Utvärdera (det här är det svåra)

```
Skriv fem frågor där du vet svaret från docs/ och kör dem mot agenten. Notera
vilka som blir fel.
```

**Fundera:** justera CHUNK till 300 och till 2000, indexera om, kör samma fem
frågor. Vilket är bäst? Kan du hitta en fråga som ser rimlig ut men där agenten
svarar fel med självförtroende?
