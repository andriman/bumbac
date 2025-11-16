from typing import Dict

from tmdb.tmdb import tmdb_episodes, tmdb_seasons, tmdb_year, years_category, movie_category, serie_category, \
    genres_category, tmdb_movie_genre, tmdb_serie_genre, tmdb_movie, tmdb_serie, search_tmdb


def tmdb_router(_handle: int, _url: str, params: Dict):
    if params["action"] == "listing_episodes":
        tmdb_episodes(_handle, _url, params["name"], params)
    elif params["action"] == "listing_seasons":
        tmdb_seasons(_handle, _url, params["name"], params["type"])
    elif params["action"] == "listing_year":
        tmdb_year(_handle, _url, params["page"], params["type"], params["id"])
    elif params["action"] == "listing_year_category":
        years_category(_handle, _url, params["name"])
    elif params["action"] == "listing_movie_category":
        movie_category(_handle, _url)
    elif params["action"] == "listing_serie_category":
        serie_category(_handle, _url)
    elif params["action"] == "listing_genre_category":
        genres_category(_handle, _url, params["name"])
    elif params["action"] == "listing_genre":
        if params["type"] == 'movie':
            tmdb_movie_genre(_handle, _url, params["page"], params["type"], params["id"])
        else:
            tmdb_serie_genre(_handle, _url, params["page"], params["type"], params["id"])
    elif params["action"] == "listing_tmdb_movie":
        tmdb_movie(_handle, _url, params["name"], params["type"])
    elif params["action"] == "listing_tmdb_serie":
        tmdb_serie(_handle, _url, params["name"], params["type"])
    elif params["action"] == "search_tmdb":
        search_tmdb(_handle, _url, params["name"], params["type"])