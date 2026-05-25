from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).parent.parent


class ConfigBase(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


class Config(ConfigBase):

    TELEGRAM_TOKEN: str
    TERMEET_DOMAIN: str
    BACKEND_API_URL: str
    WEBHOOK_SECRET_TOKEN: str
    CLAUDE_API_KEY: str = ""


config = Config()
