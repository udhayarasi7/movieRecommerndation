const STORAGE_KEY = "movierec-library";
const CHANGE_EVENT = "movierec-library-change";

const createDefaultLibrary = () => ({
    bucketLists: [{ id: "watch-later", name: "Want to Watch", movies: [] }],
    history: [],
    favorites: [],
});

export function getLibrary() {
    try {
        const stored = JSON.parse(localStorage.getItem(STORAGE_KEY));
        if (stored && Array.isArray(stored.bucketLists)) {
            return { ...createDefaultLibrary(), ...stored };
        }
    } catch {
        // Ignore invalid or unavailable local storage and use an empty library.
    }
    return createDefaultLibrary();
}

function updateLibrary(updater) {
    const next = updater(getLibrary());
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    window.dispatchEvent(new Event(CHANGE_EVENT));
    return next;
}

export function subscribeToLibrary(callback) {
    window.addEventListener(CHANGE_EVENT, callback);
    window.addEventListener("storage", callback);
    return () => {
        window.removeEventListener(CHANGE_EVENT, callback);
        window.removeEventListener("storage", callback);
    };
}

export function addToBucket(movie, listId) {
    updateLibrary((library) => {
        const targetId = listId || library.bucketLists[0]?.id;
        return {
            ...library,
            bucketLists: library.bucketLists.map((list) =>
                list.id === targetId && !list.movies.some((item) => item.movie_id === movie.movie_id)
                    ? { ...list, movies: [movie, ...list.movies] }
                    : list
            ),
        };
    });
}

export function createBucketList(name) {
    const cleanName = name.trim();
    if (!cleanName) return;
    updateLibrary((library) => ({
        ...library,
        bucketLists: [
            ...library.bucketLists,
            { id: `list-${Date.now()}`, name: cleanName, movies: [] },
        ],
    }));
}

export function addToHistory(movie) {
    updateLibrary((library) => ({
        ...library,
        history: [movie, ...library.history.filter((item) => item.movie_id !== movie.movie_id)].slice(0, 100),
    }));
}

export function toggleFavorite(movie) {
    updateLibrary((library) => {
        const exists = library.favorites.some((item) => item.movie_id === movie.movie_id);
        return {
            ...library,
            favorites: exists
                ? library.favorites.filter((item) => item.movie_id !== movie.movie_id)
                : [movie, ...library.favorites],
        };
    });
}

export function removeFromBucket(movieId, listId) {
    updateLibrary((library) => ({
        ...library,
        bucketLists: library.bucketLists.map((list) =>
            list.id === listId
                ? { ...list, movies: list.movies.filter((movie) => movie.movie_id !== movieId) }
                : list
        ),
    }));
}

export function removeFromFavorites(movieId) {
    updateLibrary((library) => ({
        ...library,
        favorites: library.favorites.filter((movie) => movie.movie_id !== movieId),
    }));
}