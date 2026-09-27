import requests
import psycopg2
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import DB_CONFIG, TMDB_API_KEY
BASE_URL = "https://api.themoviedb.org/3"

session = requests.Session()
retry = requests.packages.urllib3.util.retry.Retry(
    total=3,
    connect=3,
    read=3,
    backoff_factor=0.5,
    status_forcelist=(429, 500, 502, 503, 504),
    allowed_methods=None,
)
session.mount("https://", requests.adapters.HTTPAdapter(max_retries=retry))

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})
retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retries))

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()


def get_or_create_genre(genre_id, genre_name):
    cur.execute(
        "INSERT INTO genres (name) VALUES (%s) ON CONFLICT (name) DO NOTHING RETURNING genre_id",
        (genre_name,)
    )
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute("SELECT genre_id FROM genres WHERE name = %s", (genre_name,))
    return cur.fetchone()[0]


def insert_movie(movie, genre_map):
    cur.execute("""
        INSERT INTO movies (tmdb_id, title, overview, release_date, poster_url, imdb_rating, language)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (tmdb_id) DO NOTHING
        RETURNING movie_id
    """, (
        movie["id"],
        movie["title"],
        movie.get("overview"),
        movie.get("release_date") or None,
        f"https://image.tmdb.org/t/p/w500{movie.get('poster_path')}" if movie.get("poster_path") else None,
        movie.get("vote_average"),
        movie.get("original_language")
    ))
    row = cur.fetchone()
    if not row:
        cur.execute("SELECT movie_id FROM movies WHERE tmdb_id = %s", (movie["id"],))
        row = cur.fetchone()
    movie_id = row[0]

    # link genres
    for genre_id in movie.get("genre_ids", []):
        genre_name = genre_map.get(genre_id)
        if genre_name:
            local_genre_id = get_or_create_genre(genre_id, genre_name)
            cur.execute("""
                INSERT INTO movie_genres (movie_id, genre_id) VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """, (movie_id, local_genre_id))

    return movie_id


def fetch_genre_map():
    try:
        resp = session.get(f"{BASE_URL}/genre/movie/list", params={"api_key": TMDB_API_KEY}, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"TMDB genre request failed: {exc}") from exc

    payload = resp.json()
    if payload.get("success") is False:
        message = payload.get("status_message") or payload
        raise RuntimeError(f"TMDB genre request failed: {message}")

    genres = payload.get("genres")
    if not genres:
        raise RuntimeError(f"TMDB genre response did not contain a 'genres' list: {payload}")

    return {g["id"]: g["name"] for g in genres}


def fetch_and_store_popular_movies(pages=5):
    genre_map = fetch_genre_map()

    for page in range(1, pages + 1):
        try:
            resp = session.get(
                f"{BASE_URL}/movie/popular",
                params={"api_key": TMDB_API_KEY, "page": page},
                timeout=15,
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise RuntimeError(f"TMDB popular movies request failed on page {page}: {exc}") from exc

        data = resp.json()
        if data.get("success") is False:
            raise RuntimeError(f"TMDB popular movies request failed on page {page}: {data.get('status_message') or data}")

        for movie in data["results"]:
            insert_movie(movie, genre_map)
        conn.commit()
        print(f"Page {page} done")
        time.sleep(0.3)
def fetch_and_store_cast():
    cur.execute("SELECT movie_id, tmdb_id FROM movies")
    movies = cur.fetchall()

    for movie_id, tmdb_id in movies:
        resp = session.get(
            f"{BASE_URL}/movie/{tmdb_id}/credits",
            params={"api_key": TMDB_API_KEY}
        )
        data = resp.json()
        cast_list = data.get("cast", [])[:10]

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
        time.sleep(0.2)
        print(f"Cast stored for movie_id {movie_id}")

def fetch_and_store_tamil_movies(pages=5):
    genre_map = fetch_genre_map()
    for page in range(1, pages + 1):
        try:
            resp = session.get(f"{BASE_URL}/discover/movie", params={
                "api_key": TMDB_API_KEY,
                "with_original_language": "ta",   # ta = Tamil
                "sort_by": "popularity.desc",
                "page": page
            }, timeout=10)
            data = resp.json()
            for movie in data["results"]:
                insert_movie(movie, genre_map)
            conn.commit()
            print(f"Tamil page {page} done")
        except requests.exceptions.RequestException as e:
            print(f"Page {page} failed: {e}")
            time.sleep(2)
            continue
        time.sleep(0.3)


if __name__ == "__main__":
    fetch_and_store_tamil_movies(pages=5)


if __name__ == "__main__":
    fetch_and_store_popular_movies(pages=5)
    fetch_and_store_tamil_movies(pages=6)
    cur.close()
    conn.close()
    print("Done.")