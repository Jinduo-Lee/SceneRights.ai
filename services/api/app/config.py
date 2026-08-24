from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Locate .env by searching up directory hierarchy from current file
current_file = Path(__file__).resolve()
env_file_path = None
for parent in [current_file.parent, *current_file.parents]:
    candidate = parent / ".env"
    if candidate.is_file():
        env_file_path = candidate
        break

if env_file_path is None:
    env_file_path = Path(".env")


class Settings(BaseSettings):
    CLICKHOUSE_HOST: str = "localhost"
    CLICKHOUSE_PORT: int = 8443
    CLICKHOUSE_USER: str = "default"
    CLICKHOUSE_PASSWORD: str = ""
    CLICKHOUSE_DATABASE: str = "default"
    CLICKHOUSE_SECURE: bool = True

    DEMO_ACCESS_TOKEN: str = "demo-secret-token"
    DEMO_PROJECT_ID: str = "project_001"
    API_BASE_URL: str = "http://localhost:8000"
    APP_ENV: str = "development"

    model_config = SettingsConfigDict(
        env_file=str(env_file_path),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

