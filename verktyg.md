# Nästa lediga starttid i MinGolf

Prompts att köra en i taget mot din kodagent. Kör klart-checken efter varje steg
innan du går vidare, så har du aldrig mer än ett trasigt steg åt gången.

Förkunskap: agenten (`agent.py` + `tools.py`) fungerar, både i terminalen och i
`app.py`.

MinGolf har inget öppet API. Vi använder samma anrop som webbsidan själv gör.
Det kan sluta fungera när de ändrar sin sida, så **läs bara tider, gör aldrig
automatiska bokningar**.

---

## Steg 1 — Hitta anropet (görs för hand)

1. Logga in på mingolf.golf.se i Chrome och öppna DevTools med Cmd+Opt+I.
   Gå till fliken **Network** och filtrera på **Fetch/XHR**.
2. Gå till tidsbokningen och välj en klubb och ett datum.
3. Hitta anropet som returnerar tiderna som JSON. Högerklicka på det och välj
   **Copy → Copy as cURL**.
4. Kör kommandot i terminalen och spara svaret:
   `<din curl> > lek/mingolf_exempel.json`
5. Kolla hur klubben anges i anropet. Är det ett id i stället för namnet,
   skriv upp id:t för de klubbar du spelar på.

cURL-kommandot innehåller din inloggningscookie. Klistra inte in det i en chatt
och committa det aldrig. `lek/mingolf_exempel.json` ligger i `.gitignore`,
eftersom starttidslistan kan innehålla andra spelares namn.

Vill du ha hjälp kan du i stället ge kodagenten den här prompten:

```
Jag är inloggad på mingolf.golf.se i Chrome. Använd webbläsarverktyget, öppna
tidsbokningen för <klubb> och hitta det nätverksanrop som hämtar starttiderna.
Berätta vilken URL, vilka parametrar och vilka cookies/headers det behöver,
hur klubben anges (namn eller id), och visa hur svaret ser ut. Boka ingenting.
```

**Klart när:** `lek/mingolf_exempel.json` innehåller tider, och du vet vilken
URL, vilka parametrar, vilken cookie och vilket klubb-id anropet behöver.

---

## Steg 2 — Verktyget

```
Skriv get_next_tee_time(club, date) i tools.py. Den gör ett GET-anrop till
https://mingolf.golf.se/bokning/api/Clubs/{club_id}/CourseSchedule?courseId={course_id}&date={date}
med cookien från miljövariabeln MINGOLF_COOKIE. Återanvänd _get_json om den
finns (lägg till en headers-parameter om det behövs), annars urllib.request + json.
CLUBS = {"Wittsjö Golfklubb": ("0bfdb0f9-d311-48bf-b6ab-63ceeb80f524", "5c904943-6fec-4ebb-a659-4ca035eb736b")}
Svaret har en lista "slots". En slot är ledig om slot["availablity"]["bookable"]
är true (OBS felstavat "availablity"), slot["isLocked"] är false och
slot["availablity"]["availableSlots"] > 0. slot["time"] är UTC, t.ex.
"2026-09-15T10:30:00Z". Gör om den till Europe/Stockholm med zoneinfo.
Returnera den första lediga tiden som inte redan har passerat, som
"HH:MM, N lediga platser". Finns ingen: en tydlig text om det. Okänd klubb:
"ERROR:" och vilka klubbar som finns. 401/403: "ERROR: inloggningen har gått
ut, uppdatera MINGOLF_COOKIE". Skicka inte playersInfo vidare till modellen.
Lägg till i FUNCTIONS och SCHEMAS (club som enum av CLUBS, date som ÅÅÅÅ-MM-DD).
```

Lägg cookien i `.env` som `MINGOLF_COOKIE=...`, aldrig i koden. Den går ut
efter ett tag, och då får du hämta en ny från DevTools.

**Klart när:**
`uv run --env-file .env python -c "import tools; print(tools.get_next_tee_time('Wittsjö Golfklubb', '<datum>'))"`
ger samma första lediga tid som du ser på MinGolf.

**Fundera:** hur ska agenten veta vilket datum "i morgon" är? (Tips: den har
redan ett verktyg för det.)

---

## Steg 3 — Koppla in i agenten

```
Lägg till en rad i systemprompten i agent.py om att get_next_tee_time finns
och ska användas när användaren frågar efter lediga starttider. Använd
get_current_time först om användaren säger "i dag" eller "i morgon".
Uppdatera README:n: nytt verktyg, MINGOLF_COOKIE i .env och en exempelfråga.
```

**Klart när:** i appen ger _"finns det någon ledig tid på <klubb> i morgon?"_
🔧-rader för `get_current_time` och `get_next_tee_time`, och svaret stämmer med
MinGolf.
