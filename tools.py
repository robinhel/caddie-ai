"""Tools the agent can call, plus the schemas that describe them to the model."""

import inspect
from datetime import datetime


def get_current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


FUNCTIONS = {"get_current_time": get_current_time}


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
    }
]
