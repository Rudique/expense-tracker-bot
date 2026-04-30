from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()


@dataclass(slots=True)
class Settings:
    bot_token: str
    db_url: str
    log_level: str = "INFO"
    log_format: str = "json"  # json | pretty


def get_settings() -> Settings:
    bot_token = os.getenv("BOT_TOKEN", "")
    db_url = os.getenv("DB_URL", "sqlite+aiosqlite:///./app.db")

    if not bot_token:
        raise ValueError("BOT_TOKEN is not set")

    return Settings(
        bot_token=bot_token,
        db_url=db_url,
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        log_format=os.getenv("LOG_FORMAT", "json"),
    )