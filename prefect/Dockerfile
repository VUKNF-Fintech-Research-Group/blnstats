FROM prefecthq/prefect:3.6.11-python3.14

RUN prefect config set PREFECT_API_DATABASE_CONNECTION_URL="sqlite+aiosqlite:////prefect-data/prefect.db?timeout=30&journal_mode=WAL"
RUN prefect config set PREFECT_UI_API_URL="/prefect/api"
RUN prefect config set PREFECT_UI_SERVE_BASE="/prefect"


CMD ["prefect", "server", "start", "--host", "0.0.0.0"]