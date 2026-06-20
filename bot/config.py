from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).parent.parent


class ConfigBase(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


class RabbitMQConfig(ConfigBase):
    model_config = SettingsConfigDict(env_prefix="RABBIT_")

    HOST: str
    PORT: int
    USER: str
    PASSWORD: str

    @property
    def rb_url(self):
        return f"amqp://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/"


class Config(ConfigBase):

    TELEGRAM_TOKEN: str
    TERMEET_DOMAIN: str
    BACKEND_API_URL: str
    CLAUDE_API_KEY: str = ""
    rabbitmq: RabbitMQConfig = Field(default_factory=RabbitMQConfig)


config = Config()
