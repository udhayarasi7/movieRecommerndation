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
        movie["id"], movie["title"], movie.get("overview"),
        movie.get("release_date") or None,
        f"https://image.tmdb.org/t/p/w500{movie.get('poster_path')}" if movie.get("poster_path") else None,
        movie.get("vote_average"), movie.get("original_language")
    ))
    row = cur.fetchone()
    if not row:
        cur.execute("SELECT movie_id FROM movies WHERE tmdb_id = %s", (movie["id"],))
        row = cur.fetchone()
    movie_id = row[0]

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
    resp = session.get(f"{BASE_URL}/genre/movie/list", params={"api_key": TMDB_API_KEY}, timeout=10)
    genres = resp.json()["genres"]
    return {g["id"]: g["name"] for g in genres}


def fetch_movies_by_language(lang_code, pages=15):
    genre_map = fetch_genre_map()
    for page in range(1, pages + 1):
        try:
            resp = session.get(f"{BASE_URL}/discover/movie", params={
                "api_key": TMDB_API_KEY,
                "with_original_language": lang_code,
                "sort_by": "vote_count.desc",
                "page": page
            }, timeout=10)
            data = resp.json()
            for movie in data["results"]:
                insert_movie(movie, genre_map)
            conn.commit()
            print(f"[{lang_code}] page {page} done")
        except requests.exceptions.RequestException as e:
            print(f"[{lang_code}] page {page} failed: {e}")
            time.sleep(2)
            continue
        time.sleep(0.3)


# List every language you want in your app's language selector
LANGUAGES = ["ta", "te", "hi", "ml", "kn", "en"]
# ta=Tamil, te=Telugu, hi=Hindi, ml=Malayalam, kn=Kannada, en=English

if __name__ == "__main__":
    for lang in LANGUAGES:
        fetch_movies_by_language(lang, pages=15)
    cur.close()
    conn.close()
    print("All languages done.")