import React, { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  getTopRated,
  getNewMovies,
  getUpcomingMovies,
  getPanIndiaMovies,
  getGenres,
  getMoodList,
  getMoviesByMood,
  getMoviesByGenre,
  getMoviesByLanguage,
  getMoviesByHero,
  searchMovies,
} from "../api";
import MovieCard from "../components/MovieCard";
import SearchBar from "../components/SearchBar";

const asList = (value) => Array.isArray(value) ? value : [];

export default function Home() {
  const [searchParams, setSearchParams] = useSearchParams();
  const searchQuery = searchParams.get("q") || "";
  const [topRated, setTopRated] = useState([]);
  const [newMovies, setNewMovies] = useState([]);
  const [upcoming, setUpcoming] = useState([]);
  const [panIndia, setPanIndia] = useState([]);
  const [moods, setMoods] = useState([]);
  const [genres, setGenres] = useState([]);
  const [selectedMood, setSelectedMood] = useState(null);
  const [language, setLanguage] = useState("");
  const [moodMovies, setMoodMovies] = useState([]);
  const [searchResults, setSearchResults] = useState(null); // null = not searching
  const [searchLabel, setSearchLabel] = useState("");

  useEffect(() => {
    getTopRated().then((res) => setTopRated(asList(res.data))).catch(() => { });
    getNewMovies().then((res) => setNewMovies(asList(res.data))).catch(() => { });
    getUpcomingMovies().then((res) => setUpcoming(asList(res.data))).catch(() => { });
    getPanIndiaMovies().then((res) => setPanIndia(asList(res.data))).catch(() => { });
    getMoodList().then((res) => setMoods(asList(res.data))).catch(() => { });
    getGenres().then((res) => setGenres(asList(res.data))).catch(() => { });
  }, []);

  useEffect(() => {
    if (!searchQuery) return;
    setSearchLabel(`Search: "${searchQuery}"`);
    searchMovies(searchQuery).then((res) => setSearchResults(asList(res.data))).catch(() => setSearchResults([]));
  }, [searchQuery]);

  const loadMood = (moodName, lang = language) => {
    setSelectedMood(moodName);
    setSearchResults(null);
    getMoviesByMood(moodName, lang || undefined)
      .then((res) => setMoodMovies(asList(res.data)))
      .catch(() => setMoodMovies([]));
  };

  const handleLanguageChange = (lang) => {
    setLanguage(lang);
    if (selectedMood) loadMood(selectedMood, lang);
  };

  const handleSearchTitle = (q) => {
    setSearchParams({ q });
  };

  const handleSearchHero = (name) => {
    setSearchLabel(`Movies with "${name}"`);
    getMoviesByHero(name).then((res) => setSearchResults(asList(res.data))).catch(() => setSearchResults([]));
  };

  const handleSearchGenre = (name) => {
    setSearchLabel(`Genre: ${name}`);
    getMoviesByGenre(name).then((res) => setSearchResults(asList(res.data))).catch(() => setSearchResults([]));
  };

  const handleSearchLanguage = (code) => {
    setSearchLabel(`${code.toUpperCase()} movies`);
    getMoviesByLanguage(code).then((res) => setSearchResults(asList(res.data))).catch(() => setSearchResults([]));
  };

  const visibleSearchResults = asList(searchResults).filter((movie) =>
    !language || movie.language === language
  );

  const renderRow = (title, movies, accent = "") => (
    (() => {
      const rows = asList(movies).filter((movie) => !language || movie.language === language);
      return (
        <section className="movie-section" key={title}>
          <div className="section-heading"><h2>{title}</h2><span>{accent}</span></div>
          {rows.length ? (
            <div className="row-scroll">{rows.map((movie) => <MovieCard key={movie.movie_id} movie={movie} />)}</div>
          ) : (
            <p className="empty-msg">{language ? `No ${language.toUpperCase()} titles in this section.` : "No titles to show right now."}</p>
          )}
        </section>
      );
    })()
  );

  return (
    <div className="page home-page">
      <div className="home-intro">
        <div><p className="eyebrow">A BETTER KIND OF MOVIE NIGHT</p><h1>Find your next<br /><em>favourite film.</em></h1></div>
        <p>Fresh releases, stories worth keeping, and picks that get your mood.</p>
      </div>

      <SearchBar
        onSearchTitle={handleSearchTitle}
        onSearchHero={handleSearchHero}
        onSearchGenre={handleSearchGenre}
        onSearchLanguage={handleSearchLanguage}
        onLanguageChange={handleLanguageChange}
        genres={genres}
        initialText={searchQuery}
      />

      {searchResults !== null && (
        <>
          <div className="section-heading"><h2>{searchLabel}</h2><button className="text-button" onClick={() => { setSearchResults(null); setSearchParams({}); }}>Clear results</button></div>
          <div className="row-scroll">
            {visibleSearchResults.length > 0 ? (
              visibleSearchResults.map((m) => <MovieCard key={m.movie_id} movie={m} />)
            ) : (
              <p className="empty-msg">No results found.</p>
            )}
          </div>
        </>
      )}

      {renderRow("Coming soon", upcoming, "UPCOMING")}
      {renderRow("New on the list", newMovies, "LATEST")}
      {renderRow("Pan-India picks", panIndia, "ACROSS LANGUAGES")}
      {renderRow("Highest rated", topRated, "FAN FAVOURITES")}

      <section className="browse-section">
        <div className="section-heading"><h2>Browse by mood</h2><span>SET THE TONE</span></div>
        <div className="mood-grid">
          {moods.map((m) => (
            <button
              key={m.mood_id}
              className={`mood-btn ${selectedMood === m.name ? "active" : ""}`}
              onClick={() => loadMood(m.name)}
            >
              {m.name}
            </button>
          ))}
        </div>
      </section>

      {selectedMood && (
        <>
          <div className="section-heading"><h2>{selectedMood} {language && `· ${language.toUpperCase()}`}</h2></div>
          <div className="row-scroll">
            {moodMovies.length > 0 ? (
              moodMovies.map((m) => <MovieCard key={m.movie_id} movie={m} />)
            ) : (
              <p className="empty-msg">No movies found for this mood/language.</p>
            )}
          </div>
        </>
      )}
      <div className="home-bottom-space" />
    </div>
  );
}