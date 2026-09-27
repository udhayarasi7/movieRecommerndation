import axios from "axios";

const API_BASE = (import.meta.env.VITE_API_BASE || "http://localhost:8000").replace(/\/$/, "");

export const getTopRated = () => axios.get(`${API_BASE}/movies/top-rated`);
export const getNewMovies = () => axios.get(`${API_BASE}/movies/new`);
export const getUpcomingMovies = () => axios.get(`${API_BASE}/movies/upcoming`);
export const getPanIndiaMovies = () => axios.get(`${API_BASE}/movies/pan-india`);
export const getGenres = () => axios.get(`${API_BASE}/genres`);
export const getMoviesByGenre = (genre) =>
  axios.get(`${API_BASE}/movies/by-genre/${encodeURIComponent(genre)}`);
export const getMoviesByLanguage = (language) =>
  axios.get(`${API_BASE}/movies/by-language/${encodeURIComponent(language)}`);
export const getMoodList = () => axios.get(`${API_BASE}/moods`);
export const getMoviesByMood = (mood, language) =>
  axios.get(`${API_BASE}/movies/by-mood/${encodeURIComponent(mood)}`, {
    params: language ? { language } : {},
  });
export const getMoviesByHero = (name) =>
  axios.get(`${API_BASE}/movies/by-hero`, { params: { name } });
export const getMovieDetail = (id) => axios.get(`${API_BASE}/movies/${id}`);
export const searchMovies = (q) =>
  axios.get(`${API_BASE}/movies/search`, { params: { q } });
export const getRecommendations = (prompt) =>
  axios.post(`${API_BASE}/recommendations`, { prompt });