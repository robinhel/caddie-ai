"""Tools the agent can call, plus the schemas that describe them to the model."""

import ast
import inspect
import json
import operator
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo

import rag

OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
}


def _eval(node):
    """Walk the parse tree by hand so only arithmetic can run, never arbitrary code."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
        return OPERATORS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in OPERATORS:
        return OPERATORS[type(node.op)](_eval(node.operand))
    raise ValueError("only numbers and + - * / % ** are allowed")


def get_current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def calculate(expression):
    return _eval(ast.parse(expression, mode="eval").body)


def _get_json(url, headers=None, **params):
    req = urllib.request.Request(f"{url}?{urllib.parse.urlencode(params)}", headers=headers or {})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.load(r)


def get_weather(city):
    """Vädret just nu och en prognos på 3 dagar från Open-Meteo."""
    places = _get_json(
        "https://geocoding-api.open-meteo.com/v1/search", name=city, count=1
    ).get("results")
    if not places:
        return f"ERROR: hittade ingen plats som heter '{city}'"
    p = places[0]
    w = _get_json(
        "https://api.open-meteo.com/v1/forecast",
        latitude=p["latitude"],
        longitude=p["longitude"],
        current="temperature_2m,precipitation,wind_speed_10m,cloud_cover",
        daily="temperature_2m_max,precipitation_sum,precipitation_probability_max,wind_speed_10m_max",
        forecast_days=3,
        wind_speed_unit="ms",
        timezone="auto",
    )
    return {
        "plats": f"{p['name']}, {p.get('country', '')}",
        "nu": w["current"],
        # en dict per dag i stället för parallella listor, så modellen inte blandar ihop dagarna
        "prognos": [dict(zip(w["daily"], day)) for day in zip(*w["daily"].values())],
        "enheter": {**w["current_units"], **w["daily_units"]},
    }


STOCKHOLM = ZoneInfo("Europe/Stockholm")
# namn -> (klubb-id, bana-id), avlästa ur MinGolfs CourseSchedule-anrop i DevTools
CLUBS = {
    "Wittsjö Golfklubb": ("0bfdb0f9-d311-48bf-b6ab-63ceeb80f524", "5c904943-6fec-4ebb-a659-4ca035eb736b"),
}


def get_free_tee_times(club, date):
    """Alla lediga starttider i MinGolf som inte redan passerat. Läser bara, bokar aldrig."""
    if club not in CLUBS:
        return f"ERROR: okänd klubb '{club}'. Klubbar som finns: {', '.join(CLUBS)}"
    club_id, course_id = CLUBS[club]
    try:
        data = _get_json(
            f"https://mingolf.golf.se/bokning/api/Clubs/{club_id}/CourseSchedule",
            # funkar både med och utan "mgat=" framför värdet i .env
            headers={"Cookie": "mgat=" + os.environ.get("MINGOLF_COOKIE", "").removeprefix("mgat=")},
            courseId=course_id,
            date=date,
        )
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            return "ERROR: inloggningen har gått ut, uppdatera MINGOLF_COOKIE"
        raise
    now = datetime.now(STOCKHOLM)
    free = []
    for slot in sorted(data["slots"], key=lambda s: s["time"]):
        a = slot["availablity"]  # sic, stavat så av MinGolf
        start = datetime.fromisoformat(slot["time"]).astimezone(STOCKHOLM)
        if a["bookable"] and not slot["isLocked"] and a["availableSlots"] > 0 and start > now:
            free.append(f"{start:%H:%M} ({a['availableSlots']})")
    if not free:
        return f"Inga lediga tider på {club} {date}."
    return f"Lediga tider på {club} {date}, antal lediga platser inom parentes: {', '.join(free)}"


def search_knowledge_base(query):
    """De tre mest liknande chunksen ur docs/, som en textklump."""
    col = rag.collection()
    if col.count() == 0:
        return "ERROR: kunskapsbasen är tom. Kör 'uv run rag.py' först."
    res = col.query(query_texts=[query], n_results=3)
    return "\n---\n".join(f"[{i}]\n{d}" for i, d in zip(res["ids"][0], res["documents"][0]))


FUNCTIONS = {
    "get_current_time": get_current_time,
    "calculate": calculate,
    "get_weather": get_weather,
    "search_knowledge_base": search_knowledge_base,
    "get_free_tee_times": get_free_tee_times,
}


def call(name, args):
    """Run a tool. The model invents both the name and the arguments, so neither is trusted."""
    if name not in FUNCTIONS:
        return f"ERROR: no such tool '{name}'"
    fn = FUNCTIONS[name]
    accepted = inspect.signature(fn).parameters
    try:
        return fn(**{k: v for k, v in args.items() if k in accepted})
    except Exception as e:
        return f"ERROR: {e}"


SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Current date and time. Use when the user asks what time or what date it is.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Evaluate an arithmetic expression. Always use this instead of doing the maths yourself.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Numbers and + - * / % ** only, e.g. '47 * 213'",
                    }
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Current weather and a 3-day forecast for a city (temperature, rain, wind, cloud cover).",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string", "description": "City name"}},
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": (
                "Search the local document collection. Always search before answering "
                "questions about content that is not general knowledge, and answer only "
                "from what the search returns."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "Search query in ENGLISH, phrased with the rulebook's own terms "
                            "(e.g. 'penalty area relief', 'unplayable ball'). "
                            "Translate if the user writes in another language."
                        ),
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_free_tee_times",
            "description": (
                "All free tee times (Swedish local time) at a golf club on a given date, "
                "from MinGolf. A time missing from the list is full, blocked or already "
                "passed. Read-only, never books. Use get_current_time first if the user "
                "says 'today' or 'tomorrow'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "club": {"type": "string", "enum": list(CLUBS)},
                    "date": {"type": "string", "description": "YYYY-MM-DD"},
                },
                "required": ["club", "date"],
            },
        },
    },
]


if __name__ == "__main__":
    assert calculate("47 * 213") == 10011
    assert calculate("-2 ** 3 + 1") == -7
    assert call("calculate", {"expression": "__import__('os')"}).startswith("ERROR")
    assert call("calculate", {"expression": "1/0"}).startswith("ERROR")
    assert call("get_current_time", {"": {}}).startswith("20")
    assert call("nope", {}).startswith("ERROR")

    assert get_free_tee_times("Okänd GK", "2099-01-01").startswith("ERROR")
    # fejka MinGolf-svaret: spärrad, full, låst och ledig tid, i omvänd ordning
    slot = lambda t, bookable=True, locked=False, free=2: {
        "time": t, "isLocked": locked, "playersInfo": ["Spelare man (20,0)"],
        "availablity": {"bookable": bookable, "availableSlots": free},
    }
    _get_json = lambda *a, **k: {"slots": [
        slot("2099-06-01T09:00:00Z"),
        slot("2099-06-01T08:30:00Z", locked=True),
        slot("2099-06-01T08:10:00Z", free=0),
        slot("2099-06-01T08:00:00Z", bookable=False),
    ]}
    assert get_free_tee_times("Wittsjö Golfklubb", "2099-06-01").endswith(": 11:00 (2)")
    _get_json = lambda *a, **k: {"slots": [slot("2000-01-01T08:00:00Z")]}  # redan passerad
    assert get_free_tee_times("Wittsjö Golfklubb", "2000-01-01").startswith("Inga lediga")
    print("tools ok")
