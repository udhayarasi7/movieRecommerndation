import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import MovieCard from "../components/MovieCard";
import {
    createBucketList,
    getLibrary,
    removeFromBucket,
    removeFromFavorites,
    subscribeToLibrary,
} from "../savedMovies";

const SECTION_TITLES = {
    bucket: "Bucket lists",
    history: "Watch history",
    favorites: "Favourites",
};

export default function Library() {
    const { section = "bucket" } = useParams();
    const [library, setLibrary] = useState(getLibrary);
    const [newListName, setNewListName] = useState("");
    const [activeList, setActiveList] = useState("");

    useEffect(() => subscribeToLibrary(() => setLibrary(getLibrary())), []);

    const selectedList = library.bucketLists.find((list) => list.id === (activeList || library.bucketLists[0]?.id));
    const movies = section === "history"
        ? library.history
        : section === "favorites"
            ? library.favorites
            : selectedList?.movies || [];

    const handleCreateList = (event) => {
        event.preventDefault();
        const name = newListName.trim();
        if (!name) return;
        createBucketList(name);
        setNewListName("");
    };

    return (
        <section className="page library-page">
            <div className="page-heading">
                <div>
                    <p className="eyebrow">YOUR COLLECTION</p>
                    <h1>{SECTION_TITLES[section] || SECTION_TITLES.bucket}</h1>
                </div>
                <span className="count-label">{movies.length} {movies.length === 1 ? "movie" : "movies"}</span>
            </div>

            {section === "bucket" && (
                <>
                    <form className="create-list-form" onSubmit={handleCreateList}>
                        <input
                            aria-label="New list name"
                            placeholder="Name a new list"
                            value={newListName}
                            onChange={(event) => setNewListName(event.target.value)}
                        />
                        <button type="submit" className="primary-button">Create list</button>
                    </form>
                    <div className="list-tabs" role="tablist" aria-label="Bucket lists">
                        {library.bucketLists.map((list) => (
                            <button
                                key={list.id}
                                type="button"
                                role="tab"
                                aria-selected={(activeList || library.bucketLists[0]?.id) === list.id}
                                className={(activeList || library.bucketLists[0]?.id) === list.id ? "active" : ""}
                                onClick={() => setActiveList(list.id)}
                            >
                                {list.name} <span>{list.movies.length}</span>
                            </button>
                        ))}
                    </div>
                </>
            )}

            {movies.length ? (
                <div className="library-grid">
                    {movies.map((movie) => (
                        <div className="library-item" key={movie.movie_id}>
                            <MovieCard movie={movie} />
                            {section === "bucket" && selectedList && (
                                <button className="text-button" onClick={() => removeFromBucket(movie.movie_id, selectedList.id)}>
                                    Remove from list
                                </button>
                            )}
                            {section === "favorites" && (
                                <button className="text-button" onClick={() => removeFromFavorites(movie.movie_id)}>
                                    Remove favourite
                                </button>
                            )}
                        </div>
                    ))}
                </div>
            ) : (
                <p className="empty-state">Nothing here yet. Add movies while browsing to build this collection.</p>
            )}
        </section>
    );
}