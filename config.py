"""
Configuration module for Termeet Telegram Bot.
Loads environment variables and provides centralized config.
"""

import logging
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Telegram Bot
    TELEGRAM_TOKEN: str
    
    # Termeet
    TERMEET_DOMAIN: str
    BACKEND_API_URL: str
    
    # Security
    WEBHOOK_SECRET_TOKEN: str
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()

# Create logs directory if it doesn't exist
logs_dir = Path(__file__).parent / "logs"
logs_dir.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(logs_dir / "bot.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
