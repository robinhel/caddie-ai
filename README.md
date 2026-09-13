RUN: uv run --env-file .env agent.py

RUN: uv run --env-file .env experiment.py

RUN: uv run --env-file .env streamlit run app.py
