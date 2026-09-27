import React, { useState } from "react";
import { Link } from "react-router-dom";
import { getRecommendations } from "../api";

export default function Assistant() {
    const [isOpen, setIsOpen] = useState(false);
    const [prompt, setPrompt] = useState("");
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (event) => {
        event.preventDefault();
        const question = prompt.trim();
        if (!question || loading) return;
        setMessages((current) => [...current, { role: "user", text: question }]);
        setPrompt("");
        setLoading(true);
        try {
            const { data } = await getRecommendations(question);
            setMessages((current) => [...current, {
                role: "assistant",
                text: data.movies.length
                    ? `Try these for ${data.mood}${data.language ? ` in ${data.language.toUpperCase()}` : ""}. Search any title to open its full details.`
                    : `I found ${data.mood}${data.language ? ` in ${data.language.toUpperCase()}` : ""}, but there are no matching movies in the catalogue yet.`,
                movies: data.movies,
            }]);
        } catch (error) {
            const detail = error.response?.data?.detail;
            setMessages((current) => [...current, {
                role: "assistant",
                text: detail || "I could not reach the recommendation service. Please try again.",
            }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <>
            <button
                type="button"
                className="assistant-launcher"
                aria-label={isOpen ? "Close recommendation assistant" : "Open recommendation assistant"}
                onClick={() => setIsOpen((open) => !open)}
            >
                {isOpen ? "×" : "✦"}
            </button>
            {isOpen && (
                <aside className="assistant-panel" aria-label="Movie recommendation assistant">
                    <header className="assistant-header">
                        <div><span className="assistant-mark">✦</span><div><strong>Reel Guide</strong><small>Tell me what you feel like watching</small></div></div>
                        <button type="button" aria-label="Close assistant" onClick={() => setIsOpen(false)}>×</button>
                    </header>
                    <div className="assistant-messages" aria-live="polite">
                        {!messages.length && <p className="assistant-intro">Try “A Tamil movie about friendship”</p>}
                        {messages.map((message, index) => (
                            <div className={`chat-message ${message.role}`} key={`${index}-${message.role}`}>
                                <p>{message.text}</p>
                                {message.movies?.map((movie) => (
                                    <Link className="recommendation-link" to={`/?q=${encodeURIComponent(movie.title)}`} key={movie.movie_id} onClick={() => setIsOpen(false)}>
                                        {movie.poster_url && <img src={movie.poster_url} alt="" />}
                                        <span>{movie.title}<small>★ {movie.imdb_rating ?? "N/A"} · {movie.language?.toUpperCase() || "Language unknown"}</small></span>
                                        <b className="recommendation-search">Search</b>
                                    </Link>
                                ))}
                            </div>
                        ))}
                        {loading && <p className="assistant-status">Finding your next film...</p>}
                    </div>
                    <form className="assistant-form" onSubmit={handleSubmit}>
                        <input
                            aria-label="Describe the movie you want"
                            placeholder="A feel-good film in Tamil..."
                            value={prompt}
                            onChange={(event) => setPrompt(event.target.value)}
                        />
                        <button type="submit" aria-label="Get recommendations" disabled={loading || !prompt.trim()}>↑</button>
                    </form>
                </aside>
            )}
        </>
    );
}