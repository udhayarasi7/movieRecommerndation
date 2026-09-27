import requests
import psycopg2
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import DB_CONFIG, TMDB_API_KEY
BASE_URL = "https://api.themoviedb.org/3"

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})
retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retries))

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()


def fetch_and_store_cast():
    cur.execute("SELECT movie_id, tmdb_id FROM movies")
    movies = cur.fetchall()
    print(f"Fetching cast for {len(movies)} movies...")

    for movie_id, tmdb_id in movies:
        try:
            resp = session.get(
                f"{BASE_URL}/movie/{tmdb_id}/credits",
                params={"api_key": TMDB_API_KEY},
                timeout=10
            )
            data = resp.json()
            cast_list = data.get("cast", [])[:10]  # top 10 billed cast only

            for actor in cast_list:
                cur.execute("""
                    INSERT INTO actors (tmdb_id, name, photo_url)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (tmdb_id) DO NOTHING
                    RETURNING actor_id
                """, (
                    actor["id"],
                    actor["name"],
                    f"https://image.tmdb.org/t/p/w200{actor.get('profile_path')}" if actor.get("profile_path") else None
                ))
                row = cur.fetchone()
                if not row:
                    cur.execute("SELECT actor_id FROM actors WHERE tmdb_id = %s", (actor["id"],))
                    row = cur.fetchone()
                actor_id = row[0]

                cur.execute("""
                    INSERT INTO movie_cast (movie_id, actor_id, role_order)
                    VALUES (%s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (movie_id, actor_id, actor.get("order")))

            conn.commit()
            print(f"Cast stored for movie_id {movie_id}")
        except requests.exceptions.RequestException as e:
            print(f"Failed movie_id {movie_id}: {e}")
            time.sleep(2)
            continue
        time.sleep(0.2)


if __name__ == "__main__":
    fetch_and_store_cast()
    cur.close()
    conn.close()
    print("Done.")