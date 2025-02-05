from dotenv import load_dotenv
import os

load_dotenv()


class Settings:
    # Redis Settings
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    REDIS_TTL: int = 60 * 60 * 24  # 24 Stunden Cache-Zeit

    # API Football Settings
    API_FOOTBALL_KEY: str = os.getenv("API_FOOTBALL_KEY")
    API_FOOTBALL_URL: str = "https://v3.football.api-sports.io"
    API_FOOTBALL_HEADERS: dict = {
        'x-rapidapi-host': "api-football-v1.p.rapidapi.com",
        'x-rapidapi-key': API_FOOTBALL_KEY
    }


settings = Settings()