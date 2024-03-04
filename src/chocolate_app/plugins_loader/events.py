from typing import List, Callable, Any

ON_MOVIE_PLAY_FUNCTIONS: List[Callable[[Any], None]] = []
ON_SERIE_PLAY_FUNCTIONS: List[Callable[[Any], None]] = []
ON_MUSIC_PLAY_FUNCTIONS: List[Callable[[Any], None]] = []
ON_GAME_PLAY_FUNCTIONS: List[Callable[[Any], None]] = []
ON_BOOK_READ_FUNCTIONS: List[Callable[[Any], None]] = []
ON_LOGIN_FUNCTIONS: List[Callable[[Any], None]] = []
ON_LOGOUT_FUNCTIONS: List[Callable[[Any], None]] = []
ON_NEW_MOVIE_FUNCTIONS: List[Callable[[Any], None]] = []
ON_NEW_SERIE_FUNCTIONS: List[Callable[[Any], None]] = []
ON_NEW_SEASON_FUNCTIONS: List[Callable[[Any], None]] = []
ON_NEW_EPISODE_FUNCTIONS: List[Callable[[Any], None]] = []
ON_NEW_MUSIC_TITLE_FUNCTIONS: List[Callable[[Any], None]] = []
ON_NEW_ARTIST_FUNCTIONS: List[Callable[[Any], None]] = []
ON_NEW_ALBUM_FUNCTIONS: List[Callable[[Any], None]] = []
ON_NEW_GAME_FUNCTIONS: List[Callable[[Any], None]] = []
ON_NEW_BOOK_FUNCTIONS: List[Callable[[Any], None]] = []
ON_NEW_USER_FUNCTIONS: List[Callable[[Any], None]] = []
ON_NEW_LIBRARY_FUNCTIONS: List[Callable[[Any], None]] = []
ON_SETTINGS_CHANGE_FUNCTIONS: List[Callable[[Any], None]] = []
ON_USER_DELETE_FUNCTIONS: List[Callable[[Any], None]] = []
ON_LIBRARY_DELETE_FUNCTIONS: List[Callable[[Any], None]] = []
ON_MOVIE_EDIT_FUNCTIONS: List[Callable[[Any], None]] = []
ON_SERIE_EDIT_FUNCTIONS: List[Callable[[Any], None]] = []

def movie_play_event(*args, **kwargs) -> None:
    """Execute the functions that are listening to the movie play event"""
    for f in ON_MOVIE_PLAY_FUNCTIONS:
        f(*args, **kwargs)

def serie_play_event(*args, **kwargs) -> None:
    """Execute the functions that are listening to the serie play event"""
    for f in ON_SERIE_PLAY_FUNCTIONS:
        f(*args, **kwargs)
    
def music_play_event(*args, **kwargs) -> None:
    """Execute the functions that are listening to the music play event"""
    for f in ON_MUSIC_PLAY_FUNCTIONS:
        f(*args, **kwargs)

def game_play_event(*args, **kwargs) -> None:
    """Execute the functions that are listening to the game play event"""
    for f in ON_GAME_PLAY_FUNCTIONS:
        f(*args, **kwargs)
    
def book_read_event(*args, **kwargs) -> None:
    """Execute the functions that are listening to the book read event"""
    for f in ON_BOOK_READ_FUNCTIONS:
        f(*args, **kwargs)

def login_event(*args, **kwargs) -> None:
    """Execute the functions that are listening to the login event"""
    for f in ON_LOGIN_FUNCTIONS:
        f(*args, **kwargs)
    
"""Not implemented yet"""
def logout_event(*args, **kwargs) -> None:
    """Execute the functions that are listening to the logout event"""
    for f in ON_LOGOUT_FUNCTIONS:
        f(*args, **kwargs)

def new_movie_event(*args, **kwargs) -> None:
    """Execute the functions that are listening to the new movie event"""
    for f in ON_NEW_MOVIE_FUNCTIONS:
        f(*args, **kwargs)

def new_serie_event(*args, **kwargs) -> None:
    """Execute the functions that are listening to the new serie event"""
    for f in ON_NEW_SERIE_FUNCTIONS:
        f(*args, **kwargs)

def new_season_event(*args, **kwargs) -> None:
    """Execute the functions that are listening to the new season event"""
    for f in ON_NEW_SEASON_FUNCTIONS:
        f(*args, **kwargs)
    
def new_episode_event(*args, **kwargs) -> None:
    """Execute the functions that are listening to the new episode event"""
    for f in ON_NEW_EPISODE_FUNCTIONS:
        f(*args, **kwargs)

def new_music_title_event(*args, **kwargs) -> None:
    """Execute the functions that are listening to the new music title event"""
    for f in ON_NEW_MUSIC_TITLE_FUNCTIONS:
        f(*args, **kwargs)

def new_artist_event(*args, **kwargs) -> None:
    """Execute the functions that are listening to the new artist event"""
    for f in ON_NEW_ARTIST_FUNCTIONS:
        f(*args, **kwargs)

def new_album_event(*args, **kwargs) -> None:
    """Execute the functions that are listening to the new album event"""
    for f in ON_NEW_ALBUM_FUNCTIONS:
        f(*args, **kwargs)

def new_game_event(*args, **kwargs) -> None:
    """Execute the functions that are listening to the new game event"""
    for f in ON_NEW_GAME_FUNCTIONS:
        f(*args, **kwargs)

def new_book_event(*args, **kwargs) -> None:
    """Execute the functions that are listening to the new book event"""
    for f in ON_NEW_BOOK_FUNCTIONS:
        f(*args, **kwargs)

def new_user_event(*args, **kwargs) -> None:
    """Execute the functions that are listening to the new user event"""
    for f in ON_NEW_USER_FUNCTIONS:
        f(*args, **kwargs)

def new_library_event(*args, **kwargs) -> None:
    """Execute the functions that are listening to the new library event"""
    for f in ON_NEW_LIBRARY_FUNCTIONS:
        f(*args, **kwargs)

def settings_change_event(*args, **kwargs) -> None:
    """Execute the functions that are listening to the settings change event"""
    for f in ON_SETTINGS_CHANGE_FUNCTIONS:
        f(*args, **kwargs)

def user_delete_event(*args, **kwargs) -> None:
    """Execute the functions that are listening to the user delete event"""
    for f in ON_USER_DELETE_FUNCTIONS:
        f(*args, **kwargs)

def library_delete_event(*args, **kwargs) -> None:
    """Execute the functions that are listening to the library delete event"""
    for f in ON_LIBRARY_DELETE_FUNCTIONS:
        f(*args, **kwargs)

def movie_edit_event(*args, **kwargs) -> None:
    """Execute the functions that are listening to the movie edit event"""
    for f in ON_MOVIE_EDIT_FUNCTIONS:
        f(*args, **kwargs)

def serie_edit_event(*args, **kwargs) -> None:
    """Execute the functions that are listening to the serie edit event"""
    for f in ON_SERIE_EDIT_FUNCTIONS:
        f(*args, **kwargs)
