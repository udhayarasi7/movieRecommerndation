from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent

print("Looking for:", BASE_DIR / ".env")
print("File exists:", (BASE_DIR / ".env").exists())

load_dotenv(BASE_DIR / ".env")

print("Key found:", bool(os.getenv("GROQ_API_KEY")))