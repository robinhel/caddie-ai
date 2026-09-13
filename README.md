RUN: uv run --env-file .env agent.py

RUN: uv run --env-file .env experiment.py

INDEXERA: uv run rag.py
(måste köras om varje gång man ändrar något i docs/, annars hittar agenten inte det nya)
