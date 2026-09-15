"""Tools the agent can call, plus the schemas that describe them to the model."""

import ast
import inspect
import operator
from datetime import datetime

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


def get_weather(city):
    return f"15 degrees and sunny in {city}"


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
            "description": "Current weather in a city.",
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
]


if __name__ == "__main__":
    assert calculate("47 * 213") == 10011
    assert calculate("-2 ** 3 + 1") == -7
    assert call("calculate", {"expression": "__import__('os')"}).startswith("ERROR")
    assert call("calculate", {"expression": "1/0"}).startswith("ERROR")
    assert call("get_current_time", {"": {}}).startswith("20")
    assert call("nope", {}).startswith("ERROR")
    print("tools ok")
