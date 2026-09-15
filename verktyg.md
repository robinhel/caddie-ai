# Riktiga verktyg i småsteg

Prompts att köra en i taget mot din kodagent. Kör klart-checken efter varje steg
innan du går vidare, så har du aldrig mer än ett trasigt steg åt gången.

Förkunskap: agenten (`agent.py` + `tools.py`) fungerar, både i terminalen och i
`app.py`.

Del 1 byter ut låtsasvädret mot riktigt väder. Del 2 är extra: nästa lediga
starttid i MinGolf.

---

# Del 1 — Riktigt väder

## Steg 1 — Hämta vädret från Open-Meteo

```
get_weather i tools.py är mockad och svarar alltid "15 degrees and sunny".
Byt ut den mot riktig data från Open-Meteo (gratis, ingen API-nyckel). Använd
bara standardbiblioteket (urllib.request + json), inga nya beroenden.
Gör två anrop:
1. https://geocoding-api.open-meteo.com/v1/search?name=<stad>&count=1 för att
   få latitud och longitud.
2. https://api.open-meteo.com/v1/forecast med vädret just nu (temperatur, regn,
   vind, molnighet) och en prognos på 3 dagar (maxtemperatur, regnmängd,
   regnrisk, maxvind). Vind i m/s och timezone=auto.
Hittar geokodningen ingen plats ska funktionen returnera en sträng som börjar
med "ERROR:". Sätt timeout=10 på anropen. Returnera plats, nu och prognos.
Uppdatera verktygets description i SCHEMAS så att det står att den ger väder
just nu och en prognos på 3 dagar.
```

**Klart när:**
`uv run python -c "import tools; print(tools.get_weather('Göteborg'))"` skriver
ut riktiga siffror (jämför med en vädersajt), och
`uv run python -c "import tools; print(tools.get_weather('Xyzxyzstad'))"` ger
ett `ERROR:`.

**Fundera:** varför geokoda först, i stället för att låta modellen gissa
latitud och longitud själv?

---

## Steg 2 — Låt agenten använda prognosen

```
Nu ger get_weather en prognos på 3 dagar. Kolla att systemprompten i agent.py
säger att väderfrågor, t.ex. "blir det bra golfväder i helgen?", ska besvaras
med get_weather och inte avfärdas som något som inte handlar om golf. Svaret
ska vara kort: temperatur, regn och vind, plus en mening om det verkar vara
bra golfväder.
```

**Klart när:** i appen ger frågan *"blir det bra golfväder i Göteborg i
morgon?"* en 🔧-rad med `get_weather`, och svaret stämmer med siffrorna i den.

---

## Steg 3 — När nätet är nere

```
Vad händer om Open-Meteo inte svarar? Se till att ett nätverksfel eller en
timeout i get_weather blir ett "ERROR:"-resultat till modellen i stället för
att agenten kraschar (kolla om tools.call redan fångar det). Lägg till ett
assert längst ner i tools.py som testar att en okänd stad ger "ERROR:".
```

**Klart när:** stäng av wifi, fråga agenten om vädret. Den ska säga att den
inte kan hämta vädret just nu, inte krascha. Slå på wifi igen, och
`uv run tools.py` ska skriva `tools ok`.

**Fundera:** ska modellen få se själva felmeddelandet, eller bara "gick inte"?
Vad händer i så fall när den ska förklara för användaren?

---

# Del 2 — Nästa lediga starttid i MinGolf (extra)

MinGolf har inget öppet API. Vi använder samma anrop som webbsidan själv gör.
Det kan sluta fungera när de ändrar sin sida, så **läs bara tider, gör aldrig
automatiska bokningar**.

## Steg 4 — Hitta anropet (görs för hand)

1. Logga in på mingolf.golf.se i Chrome och öppna DevTools med Cmd+Opt+I.
   Gå till fliken **Network** och filtrera på **Fetch/XHR**.
2. Gå till tidsbokningen och välj en klubb och ett datum.
3. Hitta anropet som returnerar tiderna som JSON. Högerklicka på det och välj
   **Copy → Copy as cURL**.
4. Kör kommandot i terminalen och spara svaret:
   `<din curl> > lek/mingolf_exempel.json`

Vill du ha hjälp kan du i stället ge kodagenten den här prompten:

```
Jag är inloggad på mingolf.golf.se i Chrome. Använd webbläsarverktyget, öppna
tidsbokningen för <klubb> och hitta det nätverksanrop som hämtar starttiderna.
Berätta vilken URL, vilka parametrar och vilka cookies/headers det behöver,
och visa hur svaret ser ut. Boka ingenting.
```

**Klart när:** `lek/mingolf_exempel.json` innehåller tider, och du vet vilken
URL, vilka parametrar och vilken cookie anropet behöver.

---

## Steg 5 — Verktyget

```
Titta på lek/mingolf_exempel.json. Det är svaret från MinGolfs anrop för
starttider: <klistra in URL och parametrar från steg 4>.
Skriv get_next_tee_time(club, date) i tools.py som gör samma anrop med
urllib.request och cookien från miljövariabeln MINGOLF_COOKIE, och returnerar
den första tiden som har lediga platser och inte redan har passerat. Finns
ingen ledig tid, returnera en tydlig text om det. Om anropet ger 401/403,
returnera "ERROR: inloggningen har gått ut, uppdatera MINGOLF_COOKIE".
Lägg till den i FUNCTIONS och SCHEMAS (date som ÅÅÅÅ-MM-DD).
```

Lägg cookien i `.env` som `MINGOLF_COOKIE=...`, aldrig i koden.

**Klart när:**
`uv run --env-file .env python -c "import tools; print(tools.get_next_tee_time('<klubb>', '<datum>'))"`
ger samma första lediga tid som du ser på MinGolf.

**Fundera:** hur ska agenten veta vilket datum "i morgon" är? (Tips: den har
redan ett verktyg för det.)

---

## Steg 6 — Koppla in i agenten

```
Lägg till en rad i systemprompten i agent.py om att get_next_tee_time finns
och ska användas när användaren frågar efter lediga starttider. Använd
get_current_time först om användaren säger "i dag" eller "i morgon".
Uppdatera README:n: nytt verktyg, MINGOLF_COOKIE i .env och en exempelfråga.
```

**Klart när:** i appen ger *"finns det någon ledig tid på <klubb> i morgon?"*
🔧-rader för `get_current_time` och `get_next_tee_time`, och svaret stämmer med
MinGolf.
