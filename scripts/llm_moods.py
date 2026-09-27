from groq import Groq, RateLimitError
 
import psycopg2
import json
import time

from config import DB_CONFIG, GROQ_API_KEY

if not GROQ_API_KEY:
    raise RuntimeError("Set GROQ_API_KEY in the project .env file")

client = Groq(api_key=GROQ_API_KEY)

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

MOODS = [
    "Chill Mood", "Feel Good", "Comedy", "Rom-Com", "Romance", "Sentiment",
    "Emotional", "Family", "Friendship", "Inspirational", "Motivational",
    "Thriller", "Psychological Thriller", "Mystery", "Crime", "Horror", "Dark",
    "Sci-Fi", "Fantasy", "Adventure", "Action", "Superhero", "Survival",
    "Disaster", "Historical", "War", "Drama", "Coming-of-Age", "Teen",
    "Musical", "Sports", "Biography", "Documentary", "Suspense", "Detective",
    "Feel-Good Romance", "Dark Comedy", "Mind-Bending", "Nostalgic", "Relaxing"
]

def get_moods_for_movie(title, overview):
    prompt = f"""Tag movies by their CORE theme only.

Example 1:
Movie: Three friends reunite after years apart to fix one's failing marriage.
Correct moods: ["Friendship", "Drama", "Emotional"]

Example 2:
Movie: A detective investigates a string of murders in a small town.
Correct moods: ["Mystery", "Crime", "Suspense"]

Now tag this movie:
Movie: {title}
Overview: {overview}

Pick 2-4 moods for the CORE theme only. Return ONLY a JSON array.
Moods: {MOODS}"""

   
    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model="qwen/qwen3.8-27b",
                max_tokens=200,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )
        except RateLimitError:
            wait = 5 * (attempt + 1)
            print(f"  rate limited, waiting {wait}s...")
            time.sleep(wait)
            continue
        except Exception as e:
            print(f"  error: {e}")
            time.sleep(3)
            continue

        text = response.choices[0].message.content.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        if text:
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                pass
        time.sleep(2 * (attempt + 1))

    return []



def populate_llm_moods():
    cur.execute("SELECT mood_id, name FROM moods")
    mood_name_to_id = {name: mid for mid, name in cur.fetchall()}

    # Only get movies with NO mood tagged yet
    cur.execute("""
        SELECT m.movie_id, m.title, m.overview 
        FROM movies m
        LEFT JOIN movie_moods mm ON mm.movie_id = m.movie_id
        WHERE mm.movie_id IS NULL
    """)
    movies = cur.fetchall()
    print(f"Found {len(movies)} untagged movies")

    for movie_id, title, overview in movies:
        if not overview:
            continue
        print(f"\nProcessing: {title}")
        moods = get_moods_for_movie(title, overview)
        print(f"Tagged: {title} -> {moods}")

        for mood in moods:
            mood_id = mood_name_to_id.get(mood)
            if mood_id:
                cur.execute("""
                    INSERT INTO movie_moods (movie_id, mood_id, confidence)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (movie_id, mood_id) DO NOTHING
                """, (movie_id, mood_id, 0.90))
        conn.commit()
        time.sleep(2)

    print("LLM mood tagging completed.")
 # stay well within free-tier rate limits


if __name__ == "__main__":
    populate_llm_moods()
    cur.close()
    conn.close()