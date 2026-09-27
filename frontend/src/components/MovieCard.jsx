import React, { useState } from "react";
import { addToBucket, toggleFavorite } from "../savedMovies";

export default function MovieCard({ movie }) {
  const [flipped, setFlipped] = useState(false);

  const handleClick = () => setFlipped((f) => !f);

  const handleDoubleClick = () => {
    const trailer = movie.trailer_url || `https://www.youtube.com/results?search_query=${encodeURIComponent(`${movie.title} official trailer`)}`;
    window.open(trailer, "_blank", "noopener,noreferrer");
  };

  const stopCardClick = (event) => event.stopPropagation();

  return (
    <div
      className={`movie-card ${flipped ? "flipped" : ""}`}
      onClick={handleClick}
      onDoubleClick={handleDoubleClick}
      title="Click for details, double-click to play the trailer"
    >
      <div className="movie-card-inner">
        <div className="movie-card-face movie-card-front">
          {movie.poster_url ? (
            <img src={movie.poster_url} alt={movie.title} />
          ) : (
            <div className="poster-placeholder">{movie.title}</div>
          )}
          <div className="poster-caption"><strong>{movie.title}</strong><span>★ {movie.imdb_rating ?? "N/A"}</span></div>
        </div>

        <div className="movie-card-face movie-card-back">
          <div className="card-meta">
            <h4>{movie.title}</h4>
            <p>IMDb <strong>{movie.imdb_rating ?? "N/A"}</strong></p>
            <p>Language <strong>{movie.languages?.join(", ") || movie.language?.toUpperCase() || "Not listed"}</strong></p>
            {movie.actor_name && <p>Cast <strong>{movie.actor_name}</strong></p>}
          </div>
          <div className="card-actions" onClick={stopCardClick}>
            <button type="button" title="Add to Want to Watch" aria-label="Add to bucket list" onClick={() => addToBucket(movie)}>＋</button>
            <button type="button" title="Toggle favourite" aria-label="Toggle favourite" onClick={() => toggleFavorite(movie)}>♥</button>
          </div>
        </div>
      </div>
    </div>
  );
}