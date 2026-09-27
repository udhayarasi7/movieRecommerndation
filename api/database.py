import psycopg2
import psycopg2.extras
from config import DB_CONFIG


def get_conn():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=psycopg2.extras.RealDictCursor)