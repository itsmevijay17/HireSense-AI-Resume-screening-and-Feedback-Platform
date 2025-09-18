# backend/app/config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    MONGO_URI: str
    DB_NAME: str

    class Config:
        env_file = ".env"

settings = Settings()
