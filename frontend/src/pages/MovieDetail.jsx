import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getMovieDetail } from "../api";
import { addToBucket, addToHistory, getLibrary, toggleFavorite } from "../savedMovies";

export default function MovieDetail() {
    const { id } = useParams();
    const [movie, setMovie] = useState(null);
    const [error, setError] = useState(false);
    const [library, setLibrary] = useState(getLibrary);

    useEffect(() => {
        getMovieDetail(id)
            .then((res) => {
                setMovie(res.data);
                addToHistory(res.data);
            })
            .catch(() => setError(true));
    }, [id]);

    useEffect(() => {
        const updateLibrary = () => setLibrary(getLibrary());
        window.addEventListener("movierec-library-change", updateLibrary);
        return () => window.removeEventListener("movierec-library-change", updateLibrary);
    }, []);

    if (error) return <div className="page">Movie not found. <Link to="/" className="back-link">Go back</Link></div>;
    if (!movie) return <div className="page">Loading...</div>;

    const isFavorite = library.favorites.some((item) => item.movie_id === movie.movie_id);
    const trailer = movie.trailer_url || `https://www.youtube.com/results?search_query=${encodeURIComponent(`${movie.title} official trailer`)}`;

    return (
        <div className="page detail-page">
            <Link to="/" className="back-link">← Back to Home</Link>

            <div className="detail-hero">
                <div className="detail-poster">
                    {movie.poster_url && <img src={movie.poster_url} alt={movie.title} />}
                </div>

                <div className="detail-info">
                    <p className="eyebrow">MOVIE PROFILE</p>
                    <h1>{movie.title}</h1>
                    <p className="detail-facts">★ {movie.imdb_rating ?? "N/A"} <span>·</span> {movie.languages?.join(", ") || movie.language?.toUpperCase() || "Language not listed"} <span>·</span> {movie.release_date || "Release date unavailable"}</p>

                    <p>{movie.overview}</p>

                    <div>
                        {movie.genres?.map((g) => <span key={g} className="tag">{g}</span>)}
                    </div>
                    <div>
                        {movie.moods?.map((m) => <span key={m} className="tag">{m}</span>)}
                    </div>

                    <div className="detail-availability">
                        <p><span>PUBLIC REVIEW SENTIMENT</span><strong>{movie.public_sentiment || movie.review_sentiment || "Not available"}</strong></p>
                        <p><span>THEATRE / OTT</span><strong>{movie.availability || movie.theatre_ott || "Not listed"}</strong></p>
                    </div>
                    <div className="detail-actions">
                        <a href={trailer} target="_blank" rel="noreferrer" className="primary-button">▶ Watch trailer</a>
                        <button className="secondary-button" onClick={() => addToBucket(movie)}>＋ Want to watch</button>
                        <button className="secondary-button" onClick={() => toggleFavorite(movie)}>{isFavorite ? "♥ Favourited" : "♡ Favourite"}</button>
                        <select aria-label="Add to a bucket list" defaultValue="" onChange={(event) => {
                            if (event.target.value) addToBucket(movie, event.target.value);
                            event.target.value = "";
                        }}>
                            <option value="">Add to category…</option>
                            {library.bucketLists.map((list) => <option key={list.id} value={list.id}>{list.name}</option>)}
                        </select>
                    </div>
                </div>
            </div>

            <h2 className="section-title">Cast</h2>
            <div className="cast-row">
                {movie.cast?.map((c) => (
                    <div key={c.name} className="cast-item">
                        {c.photo_url ? (
                            <img src={c.photo_url} alt={c.name} />
                        ) : (
                            <div style={{ width: 70, height: 70, borderRadius: "50%", background: "#222" }} />
                        )}
                        <p>{c.name}</p>
                    </div>
                ))}
            </div>
        </div>
    );
}