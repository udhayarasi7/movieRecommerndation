import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DB_CONFIG = {
    "host": os.environ["DB_HOST"],
    "dbname": os.getenv("DB_NAME", "postgres"),
    "user": os.environ["DB_USER"],
    "password": os.environ["DB_PASSWORD"],
    "port": int(os.getenv("DB_PORT", "5432")),
}

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")