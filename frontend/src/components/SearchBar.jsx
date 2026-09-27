import React, { useEffect, useState } from "react";

const LANGUAGES = [
    { code: "", label: "All Languages" },
    { code: "ta", label: "Tamil" },
    { code: "te", label: "Telugu" },
    { code: "hi", label: "Hindi" },
    { code: "ml", label: "Malayalam" },
    { code: "kn", label: "Kannada" },
    { code: "en", label: "English" },
];

export default function SearchBar({ onSearchTitle, onSearchHero, onSearchGenre, onSearchLanguage, onLanguageChange, genres, initialText = "" }) {
    const [text, setText] = useState(initialText);
    const [mode, setMode] = useState("title");
    const [genre, setGenre] = useState("");
    const [language, setLanguage] = useState("");

    useEffect(() => setText(initialText), [initialText]);

    const handleSubmit = (e) => {
        e.preventDefault();
        if (mode === "genre") {
            if (genre) onSearchGenre(genre);
            return;
        }
        if (!text.trim()) {
            if (language) onSearchLanguage(language);
            return;
        }
        if (mode === "title") onSearchTitle(text.trim());
        if (mode === "hero") onSearchHero(text.trim());
    };

    return (
        <form className="search-bar" onSubmit={handleSubmit}>
            <select value={mode} onChange={(e) => setMode(e.target.value)}>
                <option value="title">Title</option>
                <option value="hero">Hero</option>
                <option value="genre">Genre</option>
            </select>
            {mode === "genre" ? (
                <select aria-label="Choose a genre" value={genre} onChange={(e) => setGenre(e.target.value)}>
                    <option value="">Choose genre</option>
                    {genres.map((item) => <option key={item.genre_id} value={item.name}>{item.name}</option>)}
                </select>
            ) : (
                <input
                    type="text"
                    placeholder={mode === "title" ? "Search movies..." : "Search by actor..."}
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                />
            )}
            <select value={language} onChange={(e) => {
                setLanguage(e.target.value);
                onLanguageChange(e.target.value);
            }}>
                {LANGUAGES.map((l) => (
                    <option key={l.code} value={l.code}>{l.label}</option>
                ))}
            </select>
            <button type="submit" className="mood-btn">Search</button>
        </form>
    );
}