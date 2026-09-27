import React from "react";
import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import Home from "./pages/Home";
import MovieDetail from "./pages/MovieDetail";
import Library from "./pages/Library";
import Assistant from "./components/Assistant";
import movieRecommendationLogo from "./assets/movie.png";

function App() {
  return (
    <div className="app-shell">
      <header className="site-header">
        <NavLink to="/" className="brand" aria-label="Movie Recommendation home">
          <img className="brand-logo" src={movieRecommendationLogo} alt="Movie Recommendation" />
        </NavLink>
        <nav className="main-nav" aria-label="Main navigation">
          <NavLink to="/" end>Discover</NavLink>
          <NavLink to="/library/bucket">Bucket list</NavLink>
          <NavLink to="/library/history">Watch history</NavLink>
          <NavLink to="/library/favorites">Favourites</NavLink>
        </nav>
        <span className="header-note">MADE FOR MOVIE PEOPLE</span>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/movie/:id" element={<MovieDetail />} />
          <Route path="/library/:section" element={<Library />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      <Assistant />
    </div>
  );
}

export default App;