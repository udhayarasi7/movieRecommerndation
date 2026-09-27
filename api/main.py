import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from database import get_conn
from groq import Groq

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
app = FastAPI(title="Movie Recommendation API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://movie-recommerndation-kappa.vercel.app/"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class RecommendationRequest(BaseModel):
    prompt: str


@app.get("/")
def root():
    return {"message": "Movie Recommendation API is running"}


# ---------- HOME PAGE ----------

@app.get("/movies/top-rated")
def top_rated(limit: int = 20):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT movie_id, title, poster_url, imdb_rating, language, release_date
        FROM movies
        WHERE imdb_rating IS NOT NULL
        ORDER BY imdb_rating DESC
        LIMIT %s
    """, (limit,))
    result = cur.fetchall()
    cur.close()
    conn.close()
    return result


@app.get("/movies/new")
def new_movies(limit: int = 20):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT movie_id, title, poster_url, imdb_rating, language, release_date
        FROM movies
        WHERE release_date IS NOT NULL
        ORDER BY release_date DESC
        LIMIT %s
    """, (limit,))
    result = cur.fetchall()
    cur.close()
    conn.close()
    return result


@app.get("/movies/by-language/{language_code}")
def movies_by_language(language_code: str, limit: int = 40):
    allowed_languages = {"ta", "te", "hi", "ml", "kn", "en"}
    if language_code not in allowed_languages:
        raise HTTPException(status_code=400, detail="Unsupported language code")

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT movie_id, title, poster_url, imdb_rating, language, release_date
        FROM movies
        WHERE language = %s
        ORDER BY imdb_rating DESC NULLS LAST, release_date DESC NULLS LAST
        LIMIT %s
    """, (language_code, limit))
    result = cur.fetchall()
    cur.close()
    conn.close()
    return result


@app.get("/movies/upcoming")
def upcoming_movies(limit: int = 20):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT movie_id, title, poster_url, imdb_rating, language, release_date
        FROM movies
        WHERE release_date > CURRENT_DATE
        ORDER BY release_date ASC
        LIMIT %s
    """, (limit,))
    result = cur.fetchall()
    cur.close()
    conn.close()
    return result


@app.get("/movies/pan-india")
def pan_india_movies(limit: int = 20):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT movie_id, title, poster_url, imdb_rating, language, release_date
        FROM movies
        WHERE language IN ('ta', 'te', 'hi', 'ml', 'kn')
        ORDER BY release_date DESC NULLS LAST, imdb_rating DESC NULLS LAST
        LIMIT %s
    """, (limit,))
    result = cur.fetchall()
    cur.close()
    conn.close()
    return result


@app.get("/genres")
def list_genres():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT genre_id, name FROM genres ORDER BY name")
    result = cur.fetchall()
    cur.close()
    conn.close()
    return result


@app.get("/movies/by-genre/{genre_name}")
def movies_by_genre(genre_name: str, limit: int = 20):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT m.movie_id, m.title, m.poster_url, m.imdb_rating, m.language, m.release_date
        FROM movies m
        JOIN movie_genres mg ON mg.movie_id = m.movie_id
        JOIN genres g ON g.genre_id = mg.genre_id
        WHERE g.name ILIKE %s
        ORDER BY m.imdb_rating DESC NULLS LAST
        LIMIT %s
    """, (genre_name, limit))
    result = cur.fetchall()
    cur.close()
    conn.close()
    return result


@app.post("/recommendations")
def recommend_movies(request: RecommendationRequest):
    api_key = GROQ_API_KEY
    if not api_key:
        raise HTTPException(status_code=503, detail="Set GROQ_API_KEY to enable natural-language recommendations")

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT name FROM moods ORDER BY name")
    mood_names = [row["name"] for row in cur.fetchall()]
    cur.close()
    conn.close()

    client = Groq(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            temperature=0,
            messages=[
                {"role": "system", "content": (
                    "Extract one best matching mood and optional language from the user's movie request. "
                    "Respond with ONLY a raw JSON object, no other text, no markdown formatting. "
                    "Return JSON with keys mood and language. mood must exactly match one of these values: "
                    f"{mood_names}. language must be one of ta, te, hi, ml, kn, en, or an empty string."
                )},
                {"role": "user", "content": request.prompt},
            ],
        )
        extracted = json.loads(response.choices[0].message.content)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"The recommendation service could not process this request: {exc}") from exc

    mood = extracted.get("mood")
    language = extracted.get("language") or ""
    if mood not in mood_names or language not in {"", "ta", "te", "hi", "ml", "kn", "en"}:
        raise HTTPException(status_code=502, detail="The recommendation service returned unsupported filters")

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT m.movie_id, m.title, m.poster_url, m.imdb_rating, m.language, m.release_date
        FROM movies m
        JOIN movie_moods mm ON mm.movie_id = m.movie_id
        JOIN moods mo ON mo.mood_id = mm.mood_id
        WHERE mo.name = %s AND (%s = '' OR m.language = %s)
        ORDER BY m.imdb_rating DESC NULLS LAST
        LIMIT 12
    """, (mood, language, language))
    movies = cur.fetchall()
    cur.close()
    conn.close()
    return {"mood": mood, "language": language, "movies": movies}


# ---------- MOODS ----------

@app.get("/moods")
def list_moods():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT mood_id, name FROM moods ORDER BY name")
    result = cur.fetchall()
    cur.close()
    conn.close()
    return result


@app.get("/movies/by-mood/{mood_name}")
def movies_by_mood(mood_name: str, language: Optional[str] = None, limit: int = 20):
    conn = get_conn()
    cur = conn.cursor()
    if language:
        cur.execute("""
            SELECT m.movie_id, m.title, m.poster_url, m.imdb_rating, m.language
            FROM movies m
            JOIN movie_moods mm ON mm.movie_id = m.movie_id
            JOIN moods mo ON mo.mood_id = mm.mood_id
            WHERE mo.name ILIKE %s AND m.language = %s
            ORDER BY m.imdb_rating DESC NULLS LAST
            LIMIT %s
        """, (mood_name, language, limit))
    else:
        cur.execute("""
            SELECT m.movie_id, m.title, m.poster_url, m.imdb_rating, m.language
            FROM movies m
            JOIN movie_moods mm ON mm.movie_id = m.movie_id
            JOIN moods mo ON mo.mood_id = mm.mood_id
            WHERE mo.name ILIKE %s
            ORDER BY m.imdb_rating DESC NULLS LAST
            LIMIT %s
        """, (mood_name, limit))
    result = cur.fetchall()
    cur.close()
    conn.close()
    if not result:
        raise HTTPException(status_code=404, detail="No movies found for this mood/language combination")
    return result


# ---------- HERO SEARCH ----------

@app.get("/movies/by-hero")
def movies_by_hero(name: str = Query(...), limit: int = 20):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT m.movie_id, m.title, m.poster_url, m.imdb_rating, m.language, a.name AS actor_name, mc.role_order
        FROM movies m
        JOIN movie_cast mc ON mc.movie_id = m.movie_id
        JOIN actors a ON a.actor_id = mc.actor_id
        WHERE a.name ILIKE %s
        ORDER BY mc.role_order ASC
        LIMIT %s
    """, (f"%{name}%", limit))
    result = cur.fetchall()
    cur.close()
    conn.close()
    if not result:
        raise HTTPException(status_code=404, detail="No movies found for this actor")
    return result


# ---------- TITLE SEARCH ----------

@app.get("/movies/search")
def search_movies(q: str, limit: int = 20):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT movie_id, title, poster_url, imdb_rating, language
        FROM movies
        WHERE title ILIKE %s
        ORDER BY imdb_rating DESC NULLS LAST
        LIMIT %s
    """, (f"%{q}%", limit))
    result = cur.fetchall()
    cur.close()
    conn.close()
    return result


# ---------- MOVIE DETAIL ----------

@app.get("/movies/{movie_id}")
def movie_detail(movie_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM movies WHERE movie_id = %s", (movie_id,))
    movie = cur.fetchone()
    if not movie:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Movie not found")

    cur.execute("""
        SELECT a.name, a.photo_url, mc.role_order
        FROM movie_cast mc
        JOIN actors a ON a.actor_id = mc.actor_id
        WHERE mc.movie_id = %s
        ORDER BY mc.role_order ASC
        LIMIT 10
    """, (movie_id,))
    cast = cur.fetchall()

    cur.execute("""
        SELECT g.name FROM movie_genres mg
        JOIN genres g ON g.genre_id = mg.genre_id
        WHERE mg.movie_id = %s
    """, (movie_id,))
    genres = [row["name"] for row in cur.fetchall()]

    cur.execute("""
        SELECT mo.name FROM movie_moods mm
        JOIN moods mo ON mo.mood_id = mm.mood_id
        WHERE mm.movie_id = %s
    """, (movie_id,))
    moods = [row["name"] for row in cur.fetchall()]

    cur.close()
    conn.close()

    movie["cast"] = cast
    movie["genres"] = genres
    movie["moods"] = moods
    return movie