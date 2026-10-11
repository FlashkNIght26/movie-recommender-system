
import os
import pickle
from pathlib import Path

import requests
import streamlit as st


# ---------------------------------------
# 1. PAGE CONFIGURATION
# ---------------------------------------
st.set_page_config(
    page_title="Movie Recommender System",
    page_icon="🎬",
    layout="wide"
)


# ---------------------------------------
# 2. FILE PATHS
# ---------------------------------------
BASE_DIR = Path(__file__).resolve().parent
MOVIES_FILE = BASE_DIR / "movies.pkl"
SIMILARITY_FILE = BASE_DIR / "similarity.pkl"


# ---------------------------------------
# 3. LOAD MOVIE DATA
# ---------------------------------------
@st.cache_resource
def load_data():
    with open(MOVIES_FILE, "rb") as file:
        movies = pickle.load(file)

    with open(SIMILARITY_FILE, "rb") as file:
        similarity = pickle.load(file)

    return movies, similarity


# ---------------------------------------
# 4. FETCH MOVIE POSTER
# ---------------------------------------
@st.cache_data(ttl=3600)
def fetch_poster(movie_id):
    api_key = os.getenv("TMDB_API_KEY")

    if not api_key:
        return None

    url = f"https://api.themoviedb.org/3/movie/{movie_id}"

    try:
        response = requests.get(
            url,
            params={
                "api_key": api_key,
                "language": "en-US"
            },
            timeout=10
        )

        response.raise_for_status()
        data = response.json()

        poster_path = data.get("poster_path")

        if poster_path:
            return (
                "https://image.tmdb.org/t/p/w500"
                + poster_path
            )

    except (requests.RequestException, ValueError):
        return None

    return None


# ---------------------------------------
# 5. RECOMMEND SIMILAR MOVIES
# ---------------------------------------
def recommend(movie):
    matching_indices = movies.index[
        movies["title"] == movie
    ].tolist()

    if not matching_indices:
        return []

    movie_index = matching_indices[0]

    distances = sorted(
        enumerate(similarity[movie_index]),
        key=lambda item: item[1],
        reverse=True
    )

    recommendations = []

    for index, score in distances:
        # Skip the selected movie
        if index == movie_index:
            continue

        movie_row = movies.iloc[index]

        recommendations.append({
            "title": movie_row["title"],
            "movie_id": movie_row["movie_id"]
        })

        if len(recommendations) == 5:
            break

    return recommendations


# ---------------------------------------
# 6. MAIN APPLICATION
# ---------------------------------------
st.title("🎬 Movie Recommender System")

st.markdown(
    "Discover movies similar to your favourites."
)


# ---------------------------------------
# 7. LOAD FILES SAFELY
# ---------------------------------------
try:
    movies, similarity = load_data()

except FileNotFoundError:
    st.error(
        "Model files are missing. Place movies.pkl and "
        "similarity.pkl in the same folder as app.py."
    )
    st.stop()

except Exception as error:
    st.error(f"Could not load the model: {error}")
    st.stop()


# ---------------------------------------
# 8. VALIDATE DATA
# ---------------------------------------
if not {"title", "movie_id"}.issubset(movies.columns):
    st.error(
        "movies.pkl must contain 'title' and 'movie_id' columns."
    )
    st.stop()

if len(movies) != len(similarity):
    st.error(
        "The number of movies and similarity scores do not match. "
        "Use the matching model files from your project."
    )
    st.stop()

movie_list = movies["title"].dropna().unique().tolist()

if not movie_list:
    st.error("No movie titles found in movies.pkl.")
    st.stop()


# ---------------------------------------
# 9. MOVIE SELECTION
# ---------------------------------------
selected_movie = st.selectbox(
    "Select a movie",
    movie_list
)


# ---------------------------------------
# 10. DISPLAY RECOMMENDATIONS
# ---------------------------------------
if st.button("Show Recommendation", type="primary"):

    with st.spinner("Finding movies for you..."):
        recommendations = recommend(selected_movie)

    if not recommendations:
        st.warning("No recommendations found.")

    else:
        st.subheader(
            f"Movies similar to {selected_movie}"
        )

        columns = st.columns(5)

        for column, movie in zip(columns, recommendations):
            with column:
                st.markdown(f"**{movie['title']}**")

                poster_url = fetch_poster(movie["movie_id"])

                if poster_url:
                    st.image(
                        poster_url,
                        use_container_width=True
                    )
                else:
                    st.caption("Poster unavailable")

st.divider()

