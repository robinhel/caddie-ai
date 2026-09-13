RUN: uv run --env-file .env agent.py

APP: uv run --env-file .env streamlit run app.py

INDEXERA: uv run rag.py
(måste köras om varje gång man ändrar något i docs/, annars hittar agenten inte det nya)
