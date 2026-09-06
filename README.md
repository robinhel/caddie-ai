RUN: uv run --env-file .env agent.py

RUN: uv run --env-file .env experiment.py

INDEXERA docs/: uv run rag.py
