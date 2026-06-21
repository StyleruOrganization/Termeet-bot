from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).parent.parent


class ConfigBase(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


class TelegramConfig(ConfigBase):
    model_config = SettingsConfigDict(env_prefix="TELEGRAM_")

    TOKEN: str
    CHAT_ID_FOR_FEEDBACK: int
    TERMEET_DOMAIN: str
    BACKEND_API_URL: str


class ClaudeConfig(ConfigBase):
    model_config = SettingsConfigDict(env_prefix="CLAUDE_")

    API_KEY: str


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

    telegram: TelegramConfig = Field(default_factory=TelegramConfig)
    claude: ClaudeConfig = Field(default_factory=ClaudeConfig)
    rabbitmq: RabbitMQConfig = Field(default_factory=RabbitMQConfig)


config = Config()
