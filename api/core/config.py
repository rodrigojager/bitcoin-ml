import os
from dotenv import load_dotenv
load_dotenv()

class Settings:
    PG_DB = os.getenv("PG_DB")
    PG_USER = os.getenv("PG_USER")
    PG_PWD = os.getenv("PG_PWD")
    PG_HOST = os.getenv("PG_HOST")
    PG_PORT = int(os.getenv("PG_PORT"))

    BINANCE_BASE = os.getenv("BINANCE_BASE")
    BINANCE_SYMBOL = os.getenv("BINANCE_SYMBOL")
    BINANCE_INTERVAL = os.getenv("BINANCE_INTERVAL")
    BINANCE_LIMIT = int(os.getenv("BINANCE_LIMIT"))
    BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

    LOOKBACK_DAYS = int(os.getenv("LOOKBACK_DAYS", "90"))
    ALPHA_DECAY = float(os.getenv("ALPHA_DECAY", "0.999"))
    REG_PATH = os.getenv("REG_PATH")
    CLS_PATH = os.getenv("CLS_PATH")

    BACKFILL_DAYS = int(os.getenv("BACKFILL_DAYS"))
    BACKFILL_SLEEP_MS = int(os.getenv("BACKFILL_SLEEP_MS"))

    # Subcaminho quando servido atrás de proxy reverso (Traefik) ex.: /fase3
    API_ROOT_PATH = os.getenv("API_PATH_PREFIX", "")

settings = Settings()

