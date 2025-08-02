FROM prefecthq/prefect:3.4.11-python3.12

RUN prefect config set PREFECT_API_DATABASE_CONNECTION_URL="sqlite+aiosqlite:////prefect.db"

CMD ["prefect", "server", "start", "--host", "0.0.0.0"]