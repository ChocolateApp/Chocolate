from pickle import GET
from typing import List, Callable, Any

OVERRIDE_MAP: dict[str, Callable[[Any], None]] = {}

SCAN_MOVIE = "scan_movie"
SCAN_SERIE = "scan_serie"
SCAN_GAME = "scan_game"
SCAN_MUSIC = "scan_music"
SCAN_BOOK = "scan_book"

GET_ALL_MOVIES = "get_all_movies"
GET_ALL_BOOKS = "get_all_books"
GET_ALL_PLAYLISTS = "get_all_playlists"
GET_ALL_ALBUMS = "get_all_albums"
GET_ALL_ARTISTS = "get_all_artists"
GET_ALL_TRACKS = "get_all_tracks"
GET_ALL_SERIES = "get_all_series"
GET_ALL_OTHERS = "get_all_others"
GET_ALL_CONSOLES = "get_all_console_game"
GET_ALL_GAMES = "get_all_games"

GET_ALBUM_TRACKS = "get_album_tracks"
GET_PLAYLIST_TRACKS = "get_playlist_tracks"

GET_TRACK = "get_track"
GET_ALBUM = "get_album"
GET_PLAYLIST = "get_playlist"
GET_ARTIST = "get_artist"

GET_ARTIST_ALBUMS = "get_artist_albums"
GET_ARTIST_TRACKS = "get_artist_tracks"

GET_MOVIE_DATA = "get_movie_data"
GET_SERIE_DATA = "get_serie_data"
GET_OTHER_DATA = "get_other_data"
GET_SEASON_DATA = "get_season_data"
GET_EPISODES = "get_episodes"
GET_EPISODE_DATA = "get_episode_data"
GET_TV = "get_tv"
GET_CHANNELS = "get_channels"
GET_ACTOR_DATA = "get_actor_data"


SEARCH_TV = "search_tv"
SEARCH_TRACKS = "search_tracks"
SEARCH_ALBUMS = "search_albums"
SEARCH_ARTISTS = "search_artists"
SEARCH_PLAYLISTS = "search_playlists"
SEARCH_MOVIES = "search_movies"
SEARCH_SERIES = "search_series"
SEARCH_BOOKS = "search_books"
SEARCH_OTHERS = "search_others"



def link(override_name: str):
    def decorator(handler):
        def wrapper(*args, **kwargs):
            return handler(*args, **kwargs)
        OVERRIDE_MAP[override_name] = wrapper
        return wrapper
    return decorator

def have_override(override_name):
    return override_name in OVERRIDE_MAP

def execute_override(override_name, *args, **kwargs) -> Any:
    from chocolate_app import app
    with app.app_context():
        if override_name in OVERRIDE_MAP:
            return OVERRIDE_MAP[override_name](*args, **kwargs)